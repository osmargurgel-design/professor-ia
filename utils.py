import re
import unicodedata
import streamlit as st


# ─── Filtros de segurança ─────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    texto = texto.lower()
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()

# Tier 1A — Hard block: termos explicitamente vulgares sem contexto educacional possível.
# Usa \b (word boundary) para não disparar em palavras maiores (ex: "cubas", "curitiba").
_TERMOS_HARD_BLOCK_EXATOS = [
    "porra", "buceta", "piroca", "xota", "xoxota",
    "boquete", "punheta", "siririca", "sacanagem",
    "foder", "fuder", "transar", "ejacular", "orgasmo",
    "sexo oral", "cu", "chupeta",
]
# Prefixos que sempre bloqueiam (masturb → masturbação, masturbar, etc.)
_TERMOS_HARD_BLOCK_PREFIXO = ["masturb"]

# Tier 1B — Ambíguos: têm uso educacional legítimo; acionam portão de confirmação.
# "pau"   → Pau Brasil (árvore nacional), Pica-Pau (pássaro)
# "gozar" → "gozar de direitos" (sociologia/direito), "gozar férias"
# "rola"  → presente de "rolar": "a bola rola" (física), "o dado rola" (matemática)
_TERMOS_AMBIGUOS_EXATOS = ["pau", "gozar", "rola"]

# Termos anatômicos (penis, vagina, vulva, anus) NÃO são filtrados aqui.
# São tratados diretamente pelo Gemini via safety_settings + system prompt científico.

# Tier 2 — frases que indicam interesse no ATO em si, não no conteúdo curricular
# Usa regex para pegar combinações mais precisas e evitar falsos positivos
_PADROES_SENSIVEIS = [
    r"como (os?|as?)?\s*\w+\s*(se\s*)?(reproduz|acasala|faz filhote|faz bebe|fazem bebe)",
    r"(de onde|como)\s+(vem|saem|nascem)\s+(os?\s*)?(bebe|crianca|filho|filhote)",
    r"como\s+(e\s+feito|sao feitos?)\s+(um\s+)?(bebe|filhote|filho)",
    r"o que e\s+(o\s+)?sexo",
    r"(pra|para)\s+que\s+serve\s+(o\s+)?sexo",
    r"como\s+funciona\s+(o\s+)?sexo",
    r"como\s+(as pessoas|os humanos|os homens|as mulheres)\s+(fazem|tem|transam|acasalam|se reproduz)",
    r"acasalamento\s+(humano|animal|dos?)",
    r"copula[cç](ao|ão)",
    r"como\s+nasce\s+um\s+bebe",
]

def checar_linguagem(pergunta: str) -> str | None:
    """Bloqueia termos explicitamente vulgares sem contexto educacional possível."""
    normalizado = _normalizar(pergunta)
    _AVISO = (
        "🧑‍🏫 Essa pergunta usa uma linguagem que não é adequada para o ambiente escolar. "
        "O Professor IA trabalha com a linguagem científica do livro didático. "
        "Consulte seu material e reformule usando os termos corretos da matéria!"
    )
    for termo in _TERMOS_HARD_BLOCK_EXATOS:
        if re.search(r'\b' + re.escape(_normalizar(termo)) + r'\b', normalizado):
            return _AVISO
    for termo in _TERMOS_HARD_BLOCK_PREFIXO:
        if re.search(r'\b' + re.escape(_normalizar(termo)), normalizado):
            return _AVISO
    return None


def checar_ambiguidade(pergunta: str) -> bool:
    """Retorna True se a pergunta contém termo ambíguo que pode ser educacional."""
    normalizado = _normalizar(pergunta)
    return any(
        re.search(r'\b' + re.escape(_normalizar(t)) + r'\b', normalizado)
        for t in _TERMOS_AMBIGUOS_EXATOS
    )

def checar_topico_sensivel(pergunta: str) -> bool:
    """Retorna True apenas quando a pergunta busca explicitamente o ATO reprodutivo,
    não para conteúdo curricular legítimo (fecundação, sistema reprodutor, etc.)."""
    normalizado = _normalizar(pergunta)
    return any(re.search(p, normalizado) for p in _PADROES_SENSIVEIS)


# ─── Inicializar session state ────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "messages": [],
        "subject": "portugues",
        "api_key": "",
        "rate_limit_until": None,
        "attached_file": None,
        "fu_key": 0,
        "pendente_sensivel": None,
        "pendente_ambiguo": None,
        "retry_pending": None,
        "error_msg": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ─── Adicionar mensagem ao histórico ─────────────────────────────────────────
def add_message(role: str, content: str, tip: str = None, sources: str = None):
    msg = {"role": role, "content": content}
    if tip:
        msg["tip"] = tip
    if sources:
        msg["sources"] = sources
    st.session_state.messages.append(msg)


# ─── Converter histórico para formato Gemini ──────────────────────────────────
def get_history_for_gemini(messages: list) -> list:
    """
    Converte o histórico interno para o formato esperado pelo Gemini:
    [{"role": "user" | "model", "parts": ["texto"]}]
    """
    history = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [{"text": msg["content"]}]})
    return history


# ─── Extrair segundos de espera do erro 429 ───────────────────────────────────
def extract_retry_seconds(error_str: str) -> int:
    """
    Tenta extrair o tempo de espera sugerido pelo Gemini no erro 429.
    Se não encontrar, retorna 60 segundos como padrão.
    """
    patterns = [
        r"retry[_\s]after[:\s]+(\d+)",
        r"wait[:\s]+(\d+)\s*second",
        r"(\d+)\s*second[s]?\s*before",
        r"retryDelay[\":\s]+(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, error_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 60  # padrão: 1 minuto


# ─── Formatar mensagem amigável de rate limit ─────────────────────────────────
def format_rate_limit_message(seconds: int) -> str:
    if seconds < 120:
        return f"muitas perguntas em pouco tempo! Aguarde **{seconds} segundos** e tente novamente. ⏳"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"muitas perguntas em pouco tempo! Aguarde **{minutes} minuto(s)** e tente novamente. ⏳"
    else:
        return (
            "o limite de uso de hoje foi atingido. 😔\n\n"
            "O Professor IA estará disponível novamente **amanhã**! "
            "Aproveite para revisar as respostas anteriores e anotar com suas próprias palavras. ✍️"
        )
