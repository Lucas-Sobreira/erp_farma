# Plan.md — ERP Farma no Databricks (Free Edition)

> Documento vivo. Atualizar o status e o registro de decisões a cada etapa concluída.
> Última atualização: 2026-10-07

## Contexto

O diagrama `images/projeto.drawio` pede: **ERP → Databricks Workflow (Landing → Bronze → Silver → Gold) → Dashboard + Chat Bot**. O cliente é do ramo de farmácia e ainda não há dados reais.

## Decisões tomadas

| Tema           | Decisão                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------- |
| Fonte de dados | Dados sintéticos de farmácia gerados pelo projeto (substituíveis depois por extração real do ERP) |
| Ambiente       | Databricks Free Edition (serverless, Unity Catalog), catálogo `erp_farma`, schemas `landing`/`bronze`/`silver`/`gold` |
| Dashboard      | AI/BI Dashboard nativo                                                                            |
| Chatbot        | Genie space sobre a Gold                                                                          |
| Deploy         | Databricks Asset Bundle (`databricks.yml`), target `dev`                                          |
| Orquestração   | Um Lakeflow Job com 3 tarefas: `gerar_landing` → `pipeline_medalhao` → `atualizar_dashboard`      |
| Medalhão       | Lakeflow Declarative Pipeline (Auto Loader, AUTO CDC, expectations)                               |
| Schemas        | `landing` (Volume `erp`), `bronze`, `silver`, `gold`                      |
| Nomenclatura   | Tabelas e colunas em português, sem acento, com comentários na Gold                               |

## Estrutura do repositório (alvo)

    databricks.yml
    resources/            farma_uc.yml, farma_pipeline.yml, farma_job.yml, farma_dashboard.yml
    src/gerador/          main.py, catalogos.py, entidades.py
    src/pipeline/bronze/  ingestao.py
    src/pipeline/silver/  tabelas.py
    src/pipeline/gold/    dimensoes.sql, fatos.sql, agregados.sql
    src/dashboards/       analise_comercial.lvdash.json
    genie/                instrucoes.md, perguntas_exemplo.md, consultas_exemplo.sql
    tests/                test_gerador.py, conferencia.sql
    pyproject.toml

## Status das etapas

Legenda: [x] feito e verificado · [~] feito, falta verificar · [ ] pendente

- [x] **0. CLAUDE.md** criado
- [x] **1. Fundação**
  - [x] `git init`, `.gitignore`, `pyproject.toml` (ambiente com `uv`, `pytest` e `ruff`)
  - [x] Instalar Databricks CLI (v1.19.0, via winget)
  - [x] `databricks auth login` no workspace Free Edition (perfil `ai_lab`)
  - [x] `databricks.yml` + `resources/farma_uc.yml` (schemas e Volume)
- [x] **2. Gerador de dados sintéticos (Landing)**
  - [x] Cadastros em CSV: `filiais`, `produtos`, `fornecedores`, `clientes`, `vendedores`
  - [x] Movimento em JSON: `vendas`, `itens_venda`, `pagamentos`, `estoque_lotes`
  - [x] Modos `backfill` e `diario` (backfill de 3 anos: ~351 mil vendas, ~808 mil itens, 345 MB, ~1 min local)
  - [x] Sujeira proposital (duplicatas, nulos, datas inválidas, itens órfãos, atualizações tardias)
  - [x] Testes `pytest` (10 testes)
- [x] **3. Bronze** — `src/pipeline/bronze/ingestao.py`
- [x] **4. Silver** — `src/pipeline/silver/tabelas.py`
- [x] **5. Gold** — `dimensoes.sql`, `fatos.sql`, `agregados.sql`
- [~] **6. Dashboard "Análise Comercial"** — 15 widgets em `analise_comercial.lvdash.json`
- [x] **7. Genie space** — instruções, relacionamentos, perguntas e SQL de referência em `genie/` (space criado pela API a partir de `genie/space.json`)
- [x] **8. Fechamento** — `CLAUDE.md` e `Readme.md` atualizados

## Verificação

- [x] `pytest` passa (determinismo, integridade referencial, sujeira esperada)
- [x] `databricks bundle validate` e `databricks bundle deploy -t dev` sem erros
- [x] `databricks bundle run farma_workflow` em `backfill` conclui as 3 tarefas
- [x] Conferências SQL (`tests/conferencia.sql`): contagem por camada, faturamento Gold = soma dos itens na Silver, nenhuma FK órfã
- [ ] Execução `diario` processa só o incremento, sem duplicar
- [ ] Dashboard abre com todos os visuais e filtros funcionando
- [x] Genie responde corretamente a 5 perguntas de exemplo

## Desvios em relação ao plano aprovado

- Silver em um único arquivo (`silver/tabelas.py`, configuração declarativa) em vez de três.
- AUTO CDC (SCD 1) em todas as tabelas Silver, não só nos cadastros: é o que deduplica o movimento e aplica cancelamentos.
- Integridade item → venda → produto validada na Gold (expectations nos fatos), não na Silver.
- Silver de clientes descarta também nome, e-mail e telefone, além de trocar o CPF por hash.
- PK/FK informativas não foram declaradas na Gold; os relacionamentos estão em `genie/instrucoes.md`. Avaliar depois da primeira execução.
- Agregado `agg_vendas_cupons_diarios` (número de vendas e ticket médio) no lugar de `agg_faturamento_mensal`.

## Riscos e pontos em aberto

- Limites da Free Edition (cota diária, 1 warehouse, limite de pipelines): se o backfill estourar, reduzir o histórico.
- Criação do Genie por API pode não estar liberada na Free Edition; nesse caso vira passo manual documentado.
- `.lvdash.json` escrito à mão é sensível a formato; validar publicando e abrindo.

## Ambiente local (verificado em 2026-10-07)

- Python 3.12.1 (pyenv-win), `uv`, git 2.41, `winget` disponíveis
- Databricks CLI v1.19.0; perfil `ai_lab` (o perfil `DEFAULT` aponta para outro workspace, com token inválido)
- Repositório git iniciado (branch `main`), nada commitado ainda

## Registro de alterações

- 2026-10-07 — `CLAUDE.md` criado; plano aprovado; ambiente local verificado.
- 2026-10-07 — Gerador implementado e testado; bundle, pipeline (Bronze/Silver/Gold), dashboard e configuração do Genie escritos, aguardando Databricks CLI e autenticação para o primeiro deploy.
- 2026-10-07 — Catálogo trocado para `erp_farma` (schemas sem o prefixo `farma_`). Deploy e backfill de 3 anos concluídos (gerador 72s, pipeline 222s). Conferências SQL OK. Genie space criado e testado com 7 perguntas; duas respostas fracas corrigidas com novas regras nas instruções (clientes não identificados e definição de crescimento). Pendente: conferir o dashboard visualmente e testar a carga `diario`.
