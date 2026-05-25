import streamlit as st
from google import genai
from google.genai import types
import time
import re
import os
import base64
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from config import SUBJECTS, SYSTEM_PROMPT_TEMPLATE, SYSTEM_PROMPT_ENEM
from utils import (
    format_rate_limit_message,
    extract_retry_seconds,
    add_message,
    get_history_for_gemini,
    init_session_state,
    checar_linguagem,
    checar_ambiguidade,
    checar_topico_sensivel,
)

VERSION = "25/05 · UI2"

def load_api_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    load_dotenv()
    return os.getenv("GEMINI_API_KEY", "")

st.set_page_config(
    page_title="Professor IA — Ensino Médio",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
    background-color: #0b0b18;
    background-image:
        radial-gradient(ellipse 700px 600px at -5% 0%,   rgba(99,102,241,0.20) 0%, transparent 65%),
        radial-gradient(ellipse 600px 500px at 105% 100%, rgba(236,72,153,0.14) 0%, transparent 65%),
        radial-gradient(ellipse 500px 400px at 75%  15%,  rgba(14,165,233,0.10) 0%, transparent 65%);
    min-height: 100vh;
}

[data-testid="stSidebar"] {
    background: rgba(9,7,22,0.96) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.82) !important; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: white !important; }

[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    margin: 6px 0 !important;
    padding: 6px 10px !important;
}
[data-testid="stChatMessage"] p  { color: rgba(255,255,255,0.88) !important; line-height: 1.75 !important; font-size: 15px !important; }
[data-testid="stChatMessage"] strong { color: #fff !important; font-weight: 600 !important; }
[data-testid="stChatMessage"] code { background: rgba(165,180,252,0.12) !important; border-radius: 5px !important; padding: 2px 7px !important; color: #a5b4fc !important; }
[data-testid="stChatMessage"] ul,
[data-testid="stChatMessage"] ol  { color: rgba(255,255,255,0.85) !important; padding-left: 20px !important; }
[data-testid="stChatMessage"] li  { margin-bottom: 4px !important; }

.tip-box {
    background: rgba(251,191,36,0.08);
    border-left: 3px solid #fbbf24;
    border-radius: 0 10px 10px 0;
    padding: 10px 15px;
    margin-top: 12px;
    font-size: 13.5px;
    color: #fde68a;
    line-height: 1.65;
}
.sources-box {
    background: rgba(99,102,241,0.08);
    border-left: 3px solid #6366f1;
    border-radius: 0 10px 10px 0;
    padding: 10px 15px;
    margin-top: 8px;
    font-size: 13px;
    color: rgba(165,180,252,0.85);
    line-height: 1.7;
}
.rate-limit-box {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.22);
    border-radius: 12px;
    padding: 14px 18px;
    color: #fca5a5;
    font-size: 14px;
    margin: 10px 0;
    line-height: 1.65;
}
.copy-btn {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.11);
    color: rgba(255,255,255,0.4);
    border-radius: 8px;
    padding: 4px 13px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 10px;
    display: inline-block;
}
.copy-btn:hover { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.38); color: #a5b4fc; }

button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    color: white !important;
}

button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.5) !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    transition: all 0.2s !important;
}
button[kind="secondary"]:hover {
    background: rgba(239,68,68,0.1) !important;
    border-color: rgba(239,68,68,0.28) !important;
    color: #fca5a5 !important;
}

/* Textarea — override completo do baseweb do Streamlit */
.stTextArea textarea,
.stTextArea [data-baseweb="base-input"],
.stTextArea [data-baseweb="textarea"],
div[data-testid="stForm"] textarea,
textarea {
    background-color: rgba(18, 16, 38, 0.95) !important;
    background: rgba(18, 16, 38, 0.95) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: rgba(255,255,255,0.92) !important;
    caret-color: #a5b4fc !important;
}
.stTextArea [data-baseweb="base-input"] {
    background-color: rgba(18, 16, 38, 0.95) !important;
    border-radius: 12px !important;
}
textarea::placeholder,
.stTextArea textarea::placeholder { color: rgba(255,255,255,0.3) !important; }
textarea:focus { outline: none !important; border-color: rgba(99,102,241,0.5) !important; }

[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: rgba(255,255,255,0.5) !important; font-size: 13.5px !important; }

.stSelectbox > div > div { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; color: white !important; }
hr { border-color: rgba(255,255,255,0.07) !important; }
p { color: rgba(255,255,255,0.82) !important; }
h1, h2, h3 { color: white !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 3px; }

/* ── Sidebar nav buttons ───────────────────────── */
[data-testid="stSidebar"] .stButton { margin-bottom: 1px !important; }
[data-testid="stSidebar"] .stButton button {
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 7px 14px !important;
    border-radius: 10px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: all 0.18s !important;
}
[data-testid="stSidebar"] button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.55) !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.07) !important;
    border: none !important;
    color: rgba(255,255,255,0.9) !important;
}
[data-testid="stSidebar"] button[kind="primary"] {
    background: rgba(99,102,241,0.18) !important;
    border: 1px solid rgba(99,102,241,0.38) !important;
    color: #a5b4fc !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
    background: rgba(99,102,241,0.28) !important;
    border-color: rgba(99,102,241,0.55) !important;
}
.sidebar-section {
    margin: 16px 0 4px 2px !important;
    color: rgba(255,255,255,0.28);
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ─── Estado e chave ───────────────────────────────────────────────────────────
init_session_state()
if not st.session_state.get("api_key"):
    st.session_state.api_key = load_api_key()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:14px 0 10px'>"
        "<span style='font-size:1.45rem;font-weight:800;"
        "background:linear-gradient(90deg,#a5b4fc,#f9a8d4);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent'>"
        "📚 Professor IA</span><br>"
        "<small style='color:rgba(255,255,255,0.30);font-size:10.5px;letter-spacing:.6px'>"
        "Ensino Médio Brasileiro</small></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<p class='sidebar-section'>📘 Matérias</p>", unsafe_allow_html=True)
    for s in SUBJECTS:
        if s["id"] in ("diversos", "enem"):
            continue
        active = st.session_state.subject == s["id"]
        if st.button(
            f"{s['emoji']}  {s['label']}",
            key=f"sb_{s['id']}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            if not active:
                st.session_state.subject = s["id"]
                st.session_state.messages = []
                st.rerun()

    st.markdown("<p class='sidebar-section'>🤖 IA & ENEM</p>", unsafe_allow_html=True)
    s_enem = next(s for s in SUBJECTS if s["id"] == "enem")
    active_enem = st.session_state.subject == "enem"
    if st.button(
        f"{s_enem['emoji']}  {s_enem['label']}",
        key="sb_enem",
        use_container_width=True,
        type="primary" if active_enem else "secondary",
    ):
        if not active_enem:
            st.session_state.subject = "enem"
            st.session_state.messages = []
            st.rerun()

    st.markdown("<p class='sidebar-section'>💬 Modo Livre</p>", unsafe_allow_html=True)
    s_div = next(s for s in SUBJECTS if s["id"] == "diversos")
    active_div = st.session_state.subject == "diversos"
    if st.button(
        f"{s_div['emoji']}  {s_div['label']}",
        key="sb_diversos",
        use_container_width=True,
        type="primary" if active_div else "secondary",
    ):
        if not active_div:
            st.session_state.subject = "diversos"
            st.session_state.messages = []
            st.rerun()

    st.markdown("<p class='sidebar-section'>📖 Como usar</p>", unsafe_allow_html=True)
    st.markdown(
        "<small style='color:rgba(255,255,255,0.40);line-height:1.9'>"
        "1. Escolha a matéria<br>"
        "2. Digite sua dúvida e clique <b>Enviar</b><br>"
        "3. Leia a explicação com atenção ✨<br>"
        "4. Anote com <b>suas próprias palavras</b> ✍️"
        "</small>",
        unsafe_allow_html=True,
    )

# ─── Cabeçalho ────────────────────────────────────────────────────────────────
current_subject = next(s for s in SUBJECTS if s["id"] == st.session_state.subject)

_brasilia = timezone(timedelta(hours=-3))
_hour = datetime.now(_brasilia).hour
_greeting = "Bom dia" if _hour < 12 else "Boa tarde" if _hour < 18 else "Boa noite"

st.markdown(
    "<h1 style='text-align:center;background:linear-gradient(90deg,#a5b4fc,#f9a8d4,#7dd3fc);"
    "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
    "font-size:2.2rem;font-weight:800;margin-bottom:2px'>📚 Professor IA</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:rgba(255,255,255,0.52);font-size:14px;text-align:center;margin:0 0 2px'>"
    f"👋 {_greeting}! Qual é a sua dúvida hoje?</p>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:rgba(255,255,255,0.30);font-size:12px;text-align:center;margin:0 0 20px'>"
    f"{current_subject['emoji']} {current_subject['label']} · Ensino Médio Brasileiro</p>",
    unsafe_allow_html=True,
)

# ─── Verificar API key ────────────────────────────────────────────────────────
if not st.session_state.get("api_key"):
    st.error("⚙️ O app não está configurado corretamente. Entre em contato com o responsável.")
    st.stop()

try:
    client = genai.Client(api_key=st.session_state.api_key)
except Exception as e:
    st.error(f"Erro ao configurar a API: {e}")
    st.stop()

# ─── Histórico de mensagens ───────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🙋"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🎓"):
            st.markdown(msg["content"])
            if msg.get("tip"):
                st.markdown(
                    f"<div class='tip-box'>💡 <strong>Dica de estudo:</strong> {msg['tip']}</div>",
                    unsafe_allow_html=True,
                )
            if msg.get("sources"):
                st.markdown(
                    f"<div class='sources-box'>📚 <strong>Fontes:</strong><br>{msg['sources'].replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True,
                )
            import urllib.parse
            wa_text = urllib.parse.quote(msg["content"])
            st.markdown(
                f"""<a class="copy-btn" href="https://wa.me/?text={wa_text}" target="_blank" style="text-decoration:none">📲 Compartilhar no WhatsApp</a>""",
                unsafe_allow_html=True,
            )

# ─── Card de boas-vindas do Modo ENEM ────────────────────────────────────────
if current_subject["id"] == "enem" and not st.session_state.messages:
    st.info(
        "🎯 **Modo ENEM — Preparatório Inteligente**\n\n"
        "Diga o que precisa e eu me adapto:\n\n"
        "📋 **Cole uma questão** (A / B / C / D / E) — analiso cada alternativa, identifico a competência ENEM e explico o raciocínio completo.\n\n"
        "🔍 **Digite apenas um tema** *(ex: Iluminismo, Fotossíntese)* — explico como o ENEM cobra aquele conteúdo e trago um exemplo de questão.\n\n"
        '🏋️ **Peça para treinar** *(ex: "me dê uma questão")* — crio uma questão estilo ENEM, aguardo sua resposta e avalio com explicação completa.'
    )

# ─── Aviso de rate limit ──────────────────────────────────────────────────────
if st.session_state.get("rate_limit_until"):
    now = datetime.now()
    if now < st.session_state.rate_limit_until:
        wait_secs = int((st.session_state.rate_limit_until - now).total_seconds())
        if wait_secs >= 3600:
            st.markdown(
                """<div class='rate-limit-box'>⚠️ <strong>Limite diário do Gemini atingido.</strong><br>
                O plano gratuito permite um número limitado de perguntas por dia.<br>
                O serviço será restabelecido automaticamente <strong>amanhã</strong>.<br>
                <small>Enquanto isso, revise as respostas anteriores e pratique com suas anotações. ✍️</small></div>""",
                unsafe_allow_html=True,
            )
        elif wait_secs >= 60:
            mins = wait_secs // 60
            st.markdown(
                f"""<div class='rate-limit-box'>⏳ <strong>Limite de requisições por minuto atingido.</strong><br>
                O sistema aceita um número limitado de perguntas por minuto.<br>
                Aguarde <strong>{mins} minuto(s)</strong> e o serviço voltará normalmente.</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div class='rate-limit-box'>⏳ Muitas requisições simultâneas. Aguarde <strong>{wait_secs} segundo(s)</strong> e tente novamente.</div>""",
                unsafe_allow_html=True,
            )
        time.sleep(1)
        st.rerun()
    else:
        st.session_state.rate_limit_until = None

# ─── Configurações de segurança da API ────────────────────────────────────────
SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_LOW_AND_ABOVE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",        threshold="BLOCK_LOW_AND_ABOVE"),
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",         threshold="BLOCK_LOW_AND_ABOVE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",  threshold="BLOCK_MEDIUM_AND_ABOVE"),
]

# ─── Função de envio ──────────────────────────────────────────────────────────
def send_question(question: str, file_data: dict = None, skip_ambiguity: bool = False):
    st.session_state.retry_pending = None  # limpa retry anterior ao enviar nova pergunta
    if st.session_state.get("rate_limit_until") and datetime.now() < st.session_state.rate_limit_until:
        st.warning("⏳ Ainda em espera. Aguarde o timer acima zerar.")
        return

    # Tier 1 — linguagem vulgar
    if question:
        aviso = checar_linguagem(question)
        if aviso:
            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(f"<div class='tip-box'>🧑‍🏫 {aviso}</div>", unsafe_allow_html=True)
            return

    # Tier 1.5 — termo ambíguo: pode ser educacional, pede confirmação antes de bloquear
    if not skip_ambiguity and question and checar_ambiguidade(question):
        st.session_state.pendente_ambiguo = {"pergunta": question, "arquivo": file_data}
        st.rerun()
        return

    # Tier 2 — tópico sensível
    if question and checar_topico_sensivel(question):
        st.session_state.pendente_sensivel = {"pergunta": question, "arquivo": file_data}
        st.rerun()
        return

    # Montar texto de exibição
    if file_data:
        icon = "📸" if file_data["type"].startswith("image") else "📄"
        label = f"{icon} `{file_data['name']}`"
        display_text = f"{label}\n{question}".strip() if question else label
    else:
        display_text = question

    add_message("user", display_text)
    with st.chat_message("user", avatar="🙋"):
        st.markdown(display_text)

    with st.chat_message("assistant", avatar="🎓"):
        stream_placeholder = st.empty()

    st.session_state.processing = True
    try:
        history = get_history_for_gemini(st.session_state.messages[:-1])

        user_parts = []
        if file_data:
            user_parts.append({
                "inline_data": {
                    "mime_type": file_data["type"],
                    "data": base64.b64encode(file_data["data"]).decode(),
                }
            })
        text_prompt = question if question else (
            f"Analise este arquivo. Identifique todas as questões escolares de {current_subject['label']} "
            "e responda cada uma de forma didática, como professor do ensino médio brasileiro. "
            "Se não houver questões escolares ou o conteúdo for inadequado, informe educadamente."
        )
        user_parts.append({"text": text_prompt})

        if current_subject["id"] == "enem":
            system_instruction = SYSTEM_PROMPT_ENEM
        else:
            system_instruction = SYSTEM_PROMPT_TEMPLATE.format(subject=current_subject["label"])
            if current_subject["id"] == "diversos":
                system_instruction += (
                    "\n\n## Modo: Assuntos Diversos\n"
                    "O aluno não selecionou uma matéria específica. Você pode responder perguntas "
                    "de qualquer disciplina do ensino médio ou dúvidas gerais do dia a dia escolar. "
                    "Identifique a área do conhecimento da pergunta e responda como especialista nela. "
                    "Mantenha sempre o foco educacional e as regras de segurança para menores."
                )
            if current_subject["id"] == "ingles":
                system_instruction += (
                    "\n\n## Matéria: Inglês — instruções específicas:\n"
                    "- SEMPRE responda em português do Brasil, pois é a língua do aluno\n"
                    "- Ao ensinar vocabulário, apresente: palavra em inglês → tradução em português → exemplo de uso\n"
                    "- Organize o conteúdo em tópicos claros com títulos\n"
                    "- Só responda em inglês se o aluno EXPLICITAMENTE pedir para praticar em inglês\n"
                    "- Seja didático: explique gramática, pronúncia e contexto de uso de cada palavra/expressão\n"
                    "- Formato de vocabulário: **palavra** (pronúncia) — tradução — 'exemplo em inglês'\n"
                )

        stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=history + [{"role": "user", "parts": user_parts}],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                safety_settings=SAFETY_SETTINGS,
                max_output_tokens=3500 if current_subject["id"] == "enem" else 2500,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )

        full_text = ""
        for chunk in stream:
            if chunk.text:
                full_text += chunk.text
                stream_placeholder.write(full_text + "▌")

        if not full_text:
            st.session_state.messages.pop()
            stream_placeholder.markdown(
                "<div class='rate-limit-box'>🛡️ A resposta foi bloqueada pelos filtros de segurança. "
                "Reformule a pergunta com linguagem acadêmica e tente novamente.</div>",
                unsafe_allow_html=True,
            )
            st.session_state.processing = False
            return

        stream_placeholder.write(full_text)

        tip = None
        tip_match = re.search(r"\[DICA\](.*?)(\[/DICA\]|$)", full_text, re.DOTALL)
        if tip_match:
            tip = tip_match.group(1).strip()
            full_text = full_text[:tip_match.start()].strip()

        sources = None
        sources_match = re.search(r"\[FONTES\](.*?)(\[/FONTES\]|$)", full_text, re.DOTALL)
        if sources_match:
            sources = sources_match.group(1).strip()
            full_text = full_text[:sources_match.start()].strip()

        add_message("assistant", full_text, tip=tip, sources=sources)
        st.session_state.rate_limit_until = None
        st.session_state.processing = False
        st.rerun()

    except Exception as e:
        st.session_state.messages.pop()
        stream_placeholder.empty()
        st.session_state.processing = False
        err_str = str(e)
        err_low = err_str.lower()

        _is_quota = (
            "429" in err_str
            or "resource_exhausted" in err_low
            or "quota" in err_low
            or "rate_limit" in err_low
            or "too_many_requests" in err_low
            or "billing" in err_low
            or "permission_denied" in err_low
            or "403" in err_str
        )
        _is_server = "503" in err_str or "unavailable" in err_low
        _is_auth = (
            "unauthenticated" in err_low
            or "api_key_invalid" in err_low
            or "invalid_api_key" in err_low
            or ("api_key" in err_low and not _is_quota)
        )

        if _is_quota:
            retry_secs = extract_retry_seconds(err_str)
            eh_cota_diaria = any(p in err_low for p in ["quota", "exhausted", "resource_exhausted", "daily", "billing", "permission_denied"])
            if retry_secs <= 60 and eh_cota_diaria:
                retry_secs = 43200  # 12 horas
            st.session_state.rate_limit_until = datetime.now() + timedelta(seconds=retry_secs)
            st.rerun()
        elif _is_server:
            st.session_state.error_msg = (
                "<div class='rate-limit-box'>🌐 <strong>Servidor ocupado no momento!</strong><br>"
                "O Gemini está com alta demanda — é temporário.<br>"
                "Use o botão <strong>🔄 Reenviar</strong> abaixo quando quiser tentar novamente.</div>"
            )
            st.session_state.retry_pending = {"question": question, "file": file_data}
            st.rerun()
        elif _is_auth:
            st.warning("😔 O Professor IA está temporariamente indisponível. Tente novamente em alguns minutos ou volte mais tarde!")
        else:
            st.session_state.error_msg = (
                "<div class='rate-limit-box'>⚠️ <strong>Falha na conexão.</strong><br>"
                "Use o botão <strong>🔄 Reenviar</strong> abaixo para tentar novamente.</div>"
            )
            st.session_state.retry_pending = {"question": question, "file": file_data}
            st.rerun()

    finally:
        # Roda sempre — inclusive quando o Streamlit interrompe o script por duplo clique.
        # Se processing ainda está True aqui, a stream foi abandonada: desfaz e limpa.
        if st.session_state.get("processing"):
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
            st.session_state.processing = False

# ─── Portão de contexto (tópico sensível) ─────────────────────────────────────
if st.session_state.get("pendente_sensivel"):
    pend = st.session_state.pendente_sensivel
    st.markdown(
        """<div class='tip-box'>🧑‍🏫 <strong>Professor IA — Antes de continuar</strong><br><br>
        Sua pergunta envolve um tema abordado de formas diferentes dependendo da série e do contexto.
        Para te ajudar do jeito certo, preciso de mais informações:</div>""",
        unsafe_allow_html=True,
    )
    with st.form("contexto_form"):
        serie = st.selectbox(
            "Qual série você está?",
            ["Selecione...", "6º ano", "7º ano", "8º ano", "9º ano",
             "1º ano EM", "2º ano EM", "3º ano EM", "Outro"],
        )
        origem = st.selectbox(
            "De onde veio essa pergunta?",
            ["Selecione...", "Exercício do professor", "Livro didático",
             "Simulado / ENEM", "Curiosidade pessoal", "Outro"],
        )
        confirmar = st.form_submit_button("Continuar", type="primary")

    if confirmar:
        series_em  = {"1º ano EM", "2º ano EM", "3º ano EM"}
        series_ef9 = {"9º ano"}
        origens_ok = {"Exercício do professor", "Livro didático", "Simulado / ENEM"}
        pode = serie in series_em or (serie in series_ef9 and origem in origens_ok)

        if serie == "Selecione..." or origem == "Selecione...":
            st.warning("Por favor, selecione sua série e a origem da pergunta.")
        elif pode and origem in origens_ok:
            q, f = pend["pergunta"], pend.get("arquivo")
            st.session_state.pendente_sensivel = None
            extra = (
                f" [Contexto: aluno do {serie}, questão de {origem}. "
                "Responda apenas no nível científico/celular adequado para essa série.]"
            )
            send_question(q + extra, f)
        else:
            st.session_state.pendente_sensivel = None
            if origem == "Curiosidade pessoal":
                msg = (
                    "Entendi que é uma curiosidade pessoal — e tudo bem ter curiosidade! 😊\n\n"
                    "O Professor IA foi criado para ajudar com o **conteúdo escolar**: "
                    "exercícios, livro didático e ENEM.\n\n"
                    "Para dúvidas sobre reprodução e sexualidade, o melhor caminho é conversar "
                    "com seu **professor de Biologia** ou seus **pais**. 💙\n\n"
                    "Se tiver dúvidas do conteúdo escolar, pode perguntar aqui!"
                )
            else:
                msg = (
                    "Para alunos do **ensino fundamental** (até o 8º ano), esse tema é melhor "
                    "abordado com o **professor de Biologia em sala de aula**. 📚\n\n"
                    "Se tiver outras dúvidas de qualquer matéria, pode perguntar aqui!"
                )
            add_message("assistant", msg)
            st.rerun()

# ─── Portão de ambiguidade (termo com duplo sentido) ─────────────────────────
if st.session_state.get("pendente_ambiguo"):
    pend = st.session_state.pendente_ambiguo
    st.markdown(
        """<div class='tip-box'>🤔 <strong>Professor IA — Confirmação de tema</strong><br><br>
        Sua pergunta contém um termo que pode ter significados diferentes.<br><br>
        <strong>Você está perguntando sobre um assunto do currículo escolar?</strong><br>
        <small>Exemplos: a árvore <em>Pau Brasil</em>, o pássaro <em>Pica-Pau</em>,
        o direito de <em>gozar</em> férias, uma bola que <em>rola</em>...</small><br><br>
        Se for um tema de estudo, confirme e o Professor IA vai interpretar no contexto educacional!</div>""",
        unsafe_allow_html=True,
    )
    col_sim, col_nao = st.columns(2)
    with col_sim:
        if st.button("✅ Sim, é um tema escolar", use_container_width=True, type="primary", key="amb_sim"):
            q = pend["pergunta"]
            f = pend.get("arquivo")
            st.session_state.pendente_ambiguo = None
            send_question(q, f, skip_ambiguity=True)
    with col_nao:
        if st.button("❌ Não é tema escolar", use_container_width=True, key="amb_nao"):
            st.session_state.pendente_ambiguo = None
            add_message(
                "assistant",
                "Tudo bem! 😊 Se tiver dúvidas sobre o conteúdo escolar, "
                "reformule a pergunta usando os termos corretos e estarei aqui para ajudar!",
            )
            st.rerun()

# ─── Erro + botão de reenvio ──────────────────────────────────────────────────
if st.session_state.get("error_msg"):
    st.markdown(st.session_state.pop("error_msg"), unsafe_allow_html=True)

if st.session_state.get("retry_pending"):
    retry = st.session_state.retry_pending
    preview = retry["question"].split("[Contexto:")[0].strip()
    preview = (preview[:70] + "…") if len(preview) > 70 else preview
    col_prev, col_retry = st.columns([5, 1])
    with col_prev:
        st.markdown(
            f"<p style='color:rgba(255,255,255,0.35);font-size:12px;margin:2px 0 6px'>↩ <em>{preview}</em></p>",
            unsafe_allow_html=True,
        )
    with col_retry:
        if st.button("🔄 Reenviar", use_container_width=True, type="primary"):
            q = st.session_state.retry_pending["question"]
            f = st.session_state.retry_pending.get("file")
            st.session_state.retry_pending = None
            send_question(q, f)

# ─── Área de input ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

_processing = st.session_state.get("processing", False)

if _processing:
    col_status, col_parar = st.columns([4, 1])
    with col_status:
        st.markdown(
            "<p style='color:rgba(165,180,252,0.75);font-size:13.5px;margin:8px 0 4px'>"
            "⏳ Professor IA está digitando...</p>",
            unsafe_allow_html=True,
        )
    with col_parar:
        if st.button("⏹ Parar", use_container_width=True, key="btn_parar"):
            # Remove a última mensagem do usuário (e eventual resposta parcial)
            msgs = st.session_state.messages
            if msgs and msgs[-1]["role"] == "assistant":
                msgs.pop()
            if msgs and msgs[-1]["role"] == "user":
                msgs.pop()
            st.session_state.processing = False
            st.rerun()

if st.session_state.messages:
    _, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("🗑️ Limpar", use_container_width=True, disabled=_processing):
            st.session_state.messages = []
            st.session_state.rate_limit_until = None
            st.rerun()

with st.expander("📎 Anexar foto do caderno ou PDF (opcional)"):
    uploaded_file = st.file_uploader(
        "Selecione imagem ou PDF",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        key=f"fu_{st.session_state.fu_key}",
        label_visibility="collapsed",
    )
    if uploaded_file:
        if uploaded_file.type.startswith("image"):
            st.image(uploaded_file.getvalue(), width=220)
            st.caption("✅ Imagem carregada — clique em Enviar abaixo")
        else:
            st.success(f"📄 **{uploaded_file.name}** carregado — clique em Enviar abaixo")
        st.session_state.attached_file = {
            "data": uploaded_file.getvalue(),
            "type": uploaded_file.type,
            "name": uploaded_file.name,
        }
    else:
        st.session_state.attached_file = None

with st.form("question_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        placeholder_text = (
            "Pergunta específica sobre o arquivo? (ou deixe em branco)"
            if st.session_state.get("attached_file")
            else f"Digite sua dúvida sobre {current_subject['label']}..."
        )
        user_input = st.text_area(
            "Sua pergunta:",
            placeholder=placeholder_text,
            height=80,
            label_visibility="collapsed",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "➤ Enviar" if not _processing else "⏳",
            use_container_width=True,
            type="primary",
            disabled=_processing,
        )

# Ao submeter: salva a pergunta, marca processing=True e faz rerun IMEDIATAMENTE.
# No próximo run o botão já nasce desabilitado — elimina a janela do duplo clique.
if submitted and (user_input.strip() or st.session_state.get("attached_file")) and not _processing:
    file_data = st.session_state.pop("attached_file", None)
    if file_data:
        st.session_state.fu_key += 1
    st.session_state.pending_question = {"question": user_input.strip(), "file": file_data}
    st.session_state.processing = True
    st.rerun()

# No run seguinte, executa a pergunta pendente (botão já está desabilitado)
if st.session_state.get("pending_question"):
    pq = st.session_state.pop("pending_question")
    send_question(pq["question"], pq.get("file"))

# ─── Rodapé ───────────────────────────────────────────────────────────────────
st.markdown(
    f"<p style='text-align:center;color:rgba(255,255,255,0.18);font-size:11px;margin-top:30px'>"
    f"Professor IA · v{VERSION} · Desenvolvido por Osmar Gurgel · Powered by Gemini · Use as respostas como apoio, não como cola! ✍️"
    f"</p>",
    unsafe_allow_html=True,
)