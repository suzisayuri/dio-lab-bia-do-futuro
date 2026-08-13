import streamlit as st

from agente import calcular_resumo_financeiro, carregar_dados, montar_system_prompt, perguntar
from config import AGENTE_NOME

st.set_page_config(page_title=AGENTE_NOME, page_icon="🧭")


@st.cache_data
def carregar_contexto():
    transacoes, perfil, produtos, _atendimentos = carregar_dados()
    resumo = calcular_resumo_financeiro(transacoes, perfil)
    system_prompt = montar_system_prompt(perfil, resumo, produtos)
    return perfil, resumo, system_prompt


perfil, resumo, system_prompt = carregar_contexto()

with st.sidebar:
    st.subheader("Cliente")
    st.write(f"**{perfil['nome']}** · {perfil['transicao_carreira']['carreira_atual']} → {perfil['transicao_carreira']['carreira_desejada']}")
    st.metric("Colchão atual", f"{resumo['meses_cobertos']} meses", f"meta: {resumo['meses_desejado']} meses")
    st.metric("Falta para a meta", f"R$ {resumo['valor_faltante']:.2f}", f"até {resumo['meta_prazo']}")

st.title(f"🧭 {AGENTE_NOME}")
st.caption("Agente financeiro para transição de carreira")

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
