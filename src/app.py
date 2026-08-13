import streamlit as st

from agente import calcular_resumo_financeiro, carregar_dados, montar_system_prompt, perguntar
from config import AGENTE_NOME

st.set_page_config(page_title=AGENTE_NOME, page_icon="🧭", layout="centered")

st.markdown(
    """
    <style>
    :root {
        --accent: #DC2626;
        --gold: #8B1A1A;
    }
    .busola-wordmark {
        text-align: center;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        color: #8A8A8A;
        margin-bottom: 6px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E1E1E 0%, #141414 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .busola-client-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 18px 16px;
        margin-bottom: 18px;
    }
    .busola-client-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F3F4F6;
        margin-bottom: 4px;
    }
    .busola-client-path {
        font-size: 0.85rem;
        color: #9CA3AF;
    }
    .busola-path-arrow {
        color: var(--gold);
        margin: 0 6px;
    }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    [data-testid="stMetricValue"] {
        color: var(--accent) !important;
    }
    .busola-hero {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 4px 0 6px 0;
    }
    .busola-badge {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.6rem;
        background: linear-gradient(135deg, var(--accent), #7F1D1D);
        box-shadow: 0 6px 18px rgba(220, 38, 38, 0.35);
        flex-shrink: 0;
    }
    .busola-hero h1 {
        margin: 0;
        font-size: 1.7rem;
        letter-spacing: -0.02em;
    }
    .busola-hero p {
        margin: 0;
        color: #9CA3AF;
        font-size: 0.95rem;
    }
    hr.busola-divider {
        border: none;
        height: 1px;
        margin: 18px 0 22px 0;
        background: linear-gradient(90deg, rgba(220, 38, 38, 0.6), rgba(255, 255, 255, 0));
    }
    [data-testid="stChatMessage"] {
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def carregar_contexto():
    transacoes, perfil, produtos, _atendimentos = carregar_dados()
    resumo = calcular_resumo_financeiro(transacoes, perfil)
    system_prompt = montar_system_prompt(perfil, resumo, produtos)
    return perfil, resumo, system_prompt


perfil, resumo, system_prompt = carregar_contexto()
transicao = perfil["transicao_carreira"]

with st.sidebar:
    st.markdown(
        f"""
        <div class="busola-client-card">
            <div class="busola-client-name">{perfil['nome']}</div>
            <div class="busola-client-path">{transicao['carreira_atual']}<span class="busola-path-arrow">→</span>{transicao['carreira_desejada']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.metric(
        "Colchão atual",
        f"{resumo['meses_cobertos']} meses",
        f"meta: {resumo['meses_desejado']} meses",
        delta_color="off",
    )
    st.progress(min(resumo["meses_cobertos"] / resumo["meses_desejado"], 1.0))
    st.metric(
        "Falta para a meta",
        f"R$ {resumo['valor_faltante']:.2f}",
        f"até {resumo['meta_prazo']}",
        delta_color="off",
    )

st.markdown(
    f"""
    <div class="busola-wordmark">Bank of Far Far Far Away</div>
    <div class="busola-hero">
        <div class="busola-badge">🧭</div>
        <div>
            <h1>{AGENTE_NOME}</h1>
            <p>Agente financeiro para transição de carreira</p>
        </div>
    </div>
    <hr class="busola-divider" />
    """,
    unsafe_allow_html=True,
)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input("Pergunte sobre sua transição de carreira...")
if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        try:
            resposta = st.write_stream(perguntar(system_prompt, st.session_state.mensagens))
        except Exception:
            resposta = (
                "Não consegui falar com o modelo local. Verifique se o Ollama está rodando "
                "(`ollama serve`) e se o modelo configurado em `config.py` foi baixado "
                "(`ollama pull llama3.1`)."
            )
            st.markdown(resposta)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
