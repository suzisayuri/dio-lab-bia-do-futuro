import json

import pandas as pd
import requests

from config import DATA_DIR, GASTOS_CORTAVEIS, OLLAMA_HOST, OLLAMA_MODEL


def carregar_dados():
    transacoes = pd.read_csv(DATA_DIR / "transacoes.csv", parse_dates=["data"])
    with open(DATA_DIR / "perfil_investidor.json", encoding="utf-8") as f:
        perfil = json.load(f)
    with open(DATA_DIR / "produtos_financeiros.json", encoding="utf-8") as f:
        produtos = json.load(f)
    atendimentos = pd.read_csv(DATA_DIR / "historico_atendimento.csv")
    return transacoes, perfil, produtos, atendimentos


def _meta_transicao(perfil):
    for meta in perfil["metas"]:
        if "transição" in meta["meta"].lower() or "transicao" in meta["meta"].lower():
            return meta
    return perfil["metas"][0]


def calcular_resumo_financeiro(transacoes, perfil):
    saidas = transacoes[transacoes["tipo"] == "saida"].copy()
    n_meses = saidas["data"].dt.to_period("M").nunique() or 1

    cortaveis = saidas[saidas["descricao"].isin(GASTOS_CORTAVEIS)]
    essenciais = saidas[~saidas["descricao"].isin(GASTOS_CORTAVEIS)]

    despesa_essencial_media = round(essenciais["valor"].sum() / n_meses, 2)
    gastos_cortaveis_medios = (
        cortaveis.groupby("descricao")["valor"].mean().round(2).to_dict()
    )

    reserva_atual = perfil["reserva_emergencia_atual"]
    meses_cobertos = round(reserva_atual / despesa_essencial_media, 1) if despesa_essencial_media else 0.0

    meses_desejado = perfil["transicao_carreira"]["meses_colchao_desejado"]
    meta = _meta_transicao(perfil)
    valor_necessario = meta["valor_necessario"]
    valor_faltante = round(max(0, valor_necessario - reserva_atual), 2)

    return {
        "despesa_essencial_media": despesa_essencial_media,
        "gastos_cortaveis_medios": gastos_cortaveis_medios,
        "reserva_atual": reserva_atual,
        "meses_cobertos": meses_cobertos,
        "meses_desejado": meses_desejado,
        "meta_valor_necessario": valor_necessario,
        "meta_prazo": meta["prazo"],
        "valor_faltante": valor_faltante,
    }


def montar_system_prompt(perfil, resumo, produtos):
    transicao = perfil["transicao_carreira"]
    cortaveis_txt = (
        "\n".join(f"  - {desc}: R$ {valor:.2f}/mês" for desc, valor in resumo["gastos_cortaveis_medios"].items())
        or "  - (nenhum identificado)"
    )
    categorias_produtos = (
        "\n".join(
            f"  - {p['categoria']} (risco {p['risco']}): {p['indicado_para']}"
            for p in produtos
            if p["risco"] == "baixo"
        )
    )

    return f"""Você é o Bússola, um agente financeiro que ajuda clientes a planejar a transição de carreira com segurança financeira.

CONTEXTO DO CLIENTE:
- Nome: {perfil['nome']}
- Perfil de investidor: {perfil['perfil_investidor']}
- Carreira atual: {transicao['carreira_atual']} -> desejada: {transicao['carreira_desejada']}
- Prazo planejado: {transicao['prazo_planejado']}

RESUMO FINANCEIRO (calculado a partir do histórico real de transações):
- Despesa essencial média: R$ {resumo['despesa_essencial_media']:.2f}/mês
- Gastos cortáveis identificados:
{cortaveis_txt}
- Reserva atual: R$ {resumo['reserva_atual']:.2f}
- Colchão atual: {resumo['meses_cobertos']} meses cobertos (meta: {resumo['meses_desejado']} meses)
- Meta de transição: R$ {resumo['meta_valor_necessario']:.2f} até {resumo['meta_prazo']} (faltam R$ {resumo['valor_faltante']:.2f})

CATEGORIAS DE PRODUTOS DE BAIXO RISCO DISPONÍVEIS (apenas para descrever, nunca recomendar um produto específico):
{categorias_produtos}

REGRAS:
1. Responda SOMENTE com base nos dados acima. Nunca estime ou invente valor que não esteja neles.
2. Se faltar um dado para responder, diga isso explicitamente e peça o dado — não arredonde nem chute.
3. Nunca recomende um investimento específico. Pode descrever categorias de forma neutra, sem dizer "compre X".
4. Nunca afirme que a transição é "segura" ou "garantida" — apresente os números e deixe a decisão com o cliente.
5. Não dê conselhos de carreira (currículo, entrevista, mercado de trabalho). Redirecione para o escopo financeiro.
6. Tom: informal-profissional, direto, sem jargão sem explicação.
"""


def perguntar(system_prompt, historico_mensagens):
    resposta = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system_prompt}, *historico_mensagens],
            "stream": True,
        },
        stream=True,
        timeout=120,
    )
    resposta.raise_for_status()
    for linha in resposta.iter_lines():
        if not linha:
            continue
        pedaco = json.loads(linha)
        conteudo = pedaco.get("message", {}).get("content", "")
        if conteudo:
            yield conteudo
