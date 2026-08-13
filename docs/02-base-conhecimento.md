# Base de Conhecimento

## Dados Utilizados

Descreva se usou os arquivos da pasta `data`, por exemplo:

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Contextualizar interações anteriores sobre a transição |
| `perfil_investidor.json` | JSON | Calcular o colchão de transição (meta, prazo, reserva atual) |
| `produtos_financeiros.json` | JSON | Descrever categorias de baixo risco para guardar a reserva |
| `transacoes.csv` | CSV | Calcular despesas essenciais e apontar gastos cortáveis |

> [!TIP]
> **Quer um dataset mais robusto?** Você pode utilizar datasets públicos do [Hugging Face](https://huggingface.co/datasets) relacionados a finanças, desde que sejam adequados ao contexto do desafio.

---

## Adaptações nos Dados

> Você modificou ou expandiu os dados mockados? Descreva aqui.

Adicionei o campo `transicao_carreira` em `perfil_investidor.json` (carreira atual, carreira desejada, prazo e meses de colchão desejado) e renomeei a meta principal para refletir isso. Incluí um atendimento sobre transição em `historico_atendimento.csv`. Expandi `transacoes.csv` de 1 para 3 meses (ago–out/2025) e adicionei a categoria `educacao` (curso de UX Design, assinatura Figma), usando como referência de categorias reais o dataset público [DoDataThings/us-bank-transaction-categories-v2](https://huggingface.co/datasets/DoDataThings/us-bank-transaction-categories-v2) (Hugging Face, MIT).

---

## Estratégia de Integração

### Como os dados são carregados?
> Descreva como seu agente acessa a base de conhecimento.

Os arquivos são lidos do disco uma vez no início da sessão do Streamlit (cache em memória) e não são relidos a cada pergunta.

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

O app pré-calcula o resumo financeiro (despesas médias, meses de colchão cobertos/faltando) a partir de `transacoes.csv` e `perfil_investidor.json`, e injeta esse resumo — não os arquivos brutos — no system prompt a cada pergunta.

---

## Exemplo de Contexto Montado

> Mostre um exemplo de como os dados são formatados para o agente.

```
Dados do Cliente:
- Nome: João Silva
- Perfil: Moderado
- Carreira atual: Analista de Sistemas → desejada: UX Designer (prazo: 2026-06)
- Reserva atual: R$ 10.000 | Meta: R$ 15.000 | Colchão desejado: 6 meses

Resumo financeiro (últimos 3 meses):
- Despesa essencial média/mês: R$ 2.150
- Colchão atual: 4,6 meses cobertos
- Gasto cortável identificado: Academia (R$ 99/mês), Assinatura Figma (R$ 45/mês)
```
