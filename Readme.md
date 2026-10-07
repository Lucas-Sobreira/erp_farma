## Profissional

Você é um Engenheiro de Dados Senior, que costuma utilizar Databricks como sua principal plataforma de Dados.
Você sabe desenvolver desde a ingestão dos dados até a entrega de valor para a área de negócio.

## Objetivos

Construir o projeto que está dentro da pasta "./images/projeto.drawio"

## O que foi construído

```
ERP (dados sintéticos) ─► Databricks Workflow ─────────────────────────┬─► AI/BI Dashboard "Análise Comercial"
                          [ Landing ─► Bronze ─► Silver ─► Gold ]      └─► Genie space (chatbot)
```

| Camada | Onde fica | O que contém |
| --- | --- | --- |
| Landing | Volume `erp_farma.landing.erp` | Arquivos como o ERP exporta: cadastros em CSV, movimento em JSON, em `<entidade>/dt=AAAA-MM-DD/` |
| Bronze | `erp_farma.bronze` | Cópia fiel em Delta, tudo como texto, com arquivo de origem e data de ingestão |
| Silver | `erp_farma.silver` | Dados tipados, validados, sem duplicatas e sem dados pessoais em claro |
| Gold | `erp_farma.gold` | Modelo estrela (`dim_*`, `fato_*`) e agregados do dashboard (`agg_*`) |

Como o cliente ainda não tem dados disponíveis, a origem é um gerador de dados fictícios de farmácia (`src/gerador`). Laboratórios, marcas, filiais, clientes, CPFs e códigos de barras são inventados.

## Como rodar

Pré-requisitos: [Databricks CLI](https://docs.databricks.com/dev-tools/cli/install.html), [uv](https://docs.astral.sh/uv/) e um workspace Databricks Free Edition.

```bash
databricks auth login --host https://<seu-workspace>.cloud.databricks.com
```

```bash
databricks bundle deploy
```

Carga inicial, com 3 anos de histórico:

```bash
databricks bundle run farma_workflow --params modo=backfill
```

Carga incremental do dia (é o padrão do job; o agendamento diário das 6h é criado pausado):

```bash
databricks bundle run farma_workflow
```

Depois da primeira carga:

- rode `tests/conferencia.sql` no SQL Editor para validar as camadas;
- abra o dashboard **Farma - Análise Comercial**;
- crie o Genie space seguindo `genie/instrucoes.md`.

## Página do assistente (Genie no site)

`web/app` é um app React + TypeScript (Vite) de perguntas e respostas ligado ao Genie space. O navegador fala só com `web/servidor.py`, que usa a credencial do Databricks CLI para chamar a Genie Conversation API; nenhum token vai para a página.

Na primeira vez, e sempre que o código de `web/app` mudar, gere a página (requer Node 20+):

```bash
npm --prefix web/app install
```

```bash
npm --prefix web/app run build
```

Depois suba o servidor e abra http://localhost:8000:

```bash
uv run --group web python web/servidor.py
```

O servidor só aceita conexões da própria máquina, porque a página mostra dados comerciais sem login.

## Desenvolvimento local

```bash
uv run pytest
```

```bash
uv run python src/gerador/main.py --modo backfill --destino _landing --anos-historico 1
```
