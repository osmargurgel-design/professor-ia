import re
import unicodedata
import streamlit as st


# ─── Filtros de segurança ─────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    texto = texto.lower()
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()

# Tier 1 — termos vulgares: bloqueia imediatamente
_TERMOS_VULGARES = [
    "penis", "vagina", "vulva", "porra", "buceta", "pau ", " pau",
    "piroca", "xota", "xoxota", "rola ", " rola", "cu ", " cu",
    "anus", "sexo oral", "boquete", "chupeta", "transar", "foder",
    "fuder", "gozar", "ejacular", "orgasmo", "masturb", "punheta",
    "siririca", "sacanagem",
]

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
    normalizado = _normalizar(pergunta)
    for termo in _TERMOS_VULGARES:
        if _normalizar(termo) in normalizado:
            return (
                "🧑‍🏫 Essa pergunta usa uma linguagem que não é adequada para o ambiente escolar. "
                "O Professor IA trabalha com a linguagem científica do livro didático. "
                "Consulte seu material e reformule usando os termos corretos da matéria!"
            )
    return None

def checar_topico_sensivel(pergunta: str) -> bool:
    """Retorna True apenas quando a pergunta busca explicitamente o ATO reprodutivo,
    não para conteúdo curricular legítimo (fecundação, sistema reprodutor, etc.)."""
    normalizado = _normalizar(pergunta)
    return any(re.search(p, normalizado) for p in _PADROES_SENSIVEIS)


# ─── Inicializar session state ────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "messages": [],
        "subject": "historia",
        "api_key": "",
        "rate_limit_until": None,
        "attached_file": None,
        "fu_key": 0,
        "pendente_sensivel": None,
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
    if seconds < 60:
        return f"um limite de requisições por minuto. Aguarde **{seconds} segundos**."
    elif seconds < 3600:
        minutes = seconds // 60
        return f"um limite diário de requisições. Aguarde **{minutes} minuto(s)**."
    else:
        hours = seconds // 3600
        return f"o limite diário atingido. Aguarde **{hours} hora(s)**."
