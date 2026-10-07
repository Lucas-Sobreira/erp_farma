# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Databricks project for a pharmacy client, built from the brief in `Readme.md` and the architecture in `images/projeto.drawio`: **ERP → Databricks Workflow (Landing → Bronze → Silver → Gold) → Dashboard + chatbot**. The client has no data available yet, so the ERP is simulated by a synthetic data generator.

Target environment is **Databricks Free Edition**: serverless only, Unity Catalog, catalog `erp_farma`, a single small SQL warehouse, and daily compute quotas. Keep data volumes and job runs modest.

Code, table names, column names and comments are in Portuguese without accents in identifiers. Keep it that way — the Gold column comments are the vocabulary Genie answers from.

## Commands

```bash
uv run pytest                                   # all tests (generator only; runs locally)
uv run pytest tests/test_gerador.py::test_reajuste_anual_de_precos   # single test
uv run ruff check . && uv run ruff format .     # lint + format
uv run python src/gerador/main.py --modo backfill --destino _landing --anos-historico 1   # generate files locally

uv run --group web python web/servidor.py        # assistant web page at http://localhost:8000

databricks bundle validate
databricks bundle deploy                                      # target dev is the default
databricks bundle run farma_workflow --params modo=backfill   # initial load (3 years)
databricks bundle run farma_workflow                          # daily incremental load
```

The Databricks CLI authenticates through a profile created by the user with `databricks auth login`; the bundle picks the profile whose host matches `databricks.yml`. For non-bundle commands (`databricks genie ...`, `databricks api ...`) pass `-p ai_lab`, because the `DEFAULT` profile on this machine points to another workspace.

Only the generator is testable locally. The pipeline (Bronze/Silver/Gold) runs only in the workspace; validate changes by deploying, running the job, and running `tests/conferencia.sql` in the SQL Editor (each query states its expected result).

## Architecture

Everything is deployed by one Databricks Asset Bundle (`databricks.yml` + `resources/*.yml`). Resource names reference each other through `${resources...}` so schema names are defined once, in `resources/farma_uc.yml`.

**Job `farma_workflow`** (`resources/farma_job.yml`) runs three tasks in sequence:

1. `gerar_landing` — `src/gerador/main.py` writes files to the Volume `landing.erp`.
2. `pipeline_medalhao` — the Lakeflow Declarative Pipeline `farma_medalhao`.
3. `atualizar_dashboard` — refreshes the AI/BI dashboard.

**Generator (`src/gerador`)** — standard library only, flat imports (`import catalogos`), because it runs as a plain script task; `pyproject.toml` puts `src/gerador` on the pytest path for the same reason.
- Fully deterministic: every random draw comes from `Gerador._rng(...)`, seeded by (seed, entity, date). A given day's sales are identical in `backfill` and `diario` modes. Do not introduce unseeded randomness or order-dependent state.
- Money is computed in integer cents and converted at the end, so sale totals equal the sum of items exactly.
- Output layout is `<entidade>/dt=<extraction date>/`. `dt` is when the export ran, not the business date; backfill writes one movement file per month under a single `dt`.
- Master data (cadastros) is CSV with `;` separator and comma decimals; movement is JSON Lines.
- It injects deliberate defects (duplicates, nulls, bad dates, orphan items, messy whitespace/case). Each defect has a matching fix or expectation in Silver/Gold — add them in pairs.

**Pipeline (`src/pipeline`)** — all files under this folder are loaded by the pipeline (glob in `resources/farma_pipeline.yml`). Schema names arrive as pipeline configuration (`farma.landing`, `farma.schema_bronze`, `farma.schema_silver`), read with `spark.conf.get` in Python and `${farma.schema_silver}` in SQL. Gold is the pipeline's default schema, so Gold tables are declared unqualified.
- `bronze/ingestao.py` — one Auto Loader streaming table per entity, all columns as strings, no business rules.
- `silver/tabelas.py` — a declarative `ENTIDADES` dict (columns as SQL expressions, expectations, keys, sequence column) drives a generic loop: cleaned temporary view with `expect_all_or_drop` → `create_auto_cdc_flow` (SCD type 1). CDC is what deduplicates and applies late master-data changes and sale cancellations. Personal data stops here: client name/e-mail/phone are dropped and CPF is hashed.
- `gold/*.sql` — materialized views with explicit column lists (type + comment). The `SELECT` must match the column list in order and type. Referential integrity is enforced in the facts: LEFT JOINs take keys from the master-data side, so orphans violate an expectation and are dropped (and counted in pipeline metrics). `fato_vendas` is at sale-item grain and contains only concluded sales.

**Dashboard** — `src/dashboards/analise_comercial.lvdash.json`. Its queries use unqualified table names; catalog and schema come from `dataset_catalog`/`dataset_schema` in `resources/farma_dashboard.yml`. Filters work because every `agg_*` table keeps `data_venda`, `canal` and `nome_filial`.

**Chatbot** — a Genie space over the Gold `dim_*`/`fato_*` tables (not `agg_*`). It is not deployed by the bundle; `genie/` holds its instructions, joins, sample questions and reference SQL as the source of truth, and `genie/montar_space.py` turns them into the API payload.

**Web page (`web/`)** — `index.html` (single file, no build step, no JS dependencies) plus `servidor.py`, a standard-library HTTP server that proxies the Genie Conversation API through `databricks-sdk` using the CLI profile (`DATABRICKS_CONFIG_PROFILE`, default `ai_lab`; `GENIE_SPACE_ID` overrides the space). The browser never sees a Databricks token. Flow: `POST /api/perguntar` starts a conversation or adds a follow-up message and returns ids; the page polls `GET /api/resposta` until the message reaches a final state, then renders text, result table, SQL and follow-up suggestions. The page builds DOM nodes with `textContent` only — never inject Genie output as HTML. The server binds to loopback only (both `127.0.0.1` and `::1`) because the page has no login; do not bind it to a public interface without adding authentication. `web/` is excluded from bundle sync and has its own dependency group (`web`).

## Status

Deployed to the user's Free Edition workspace (CLI profile `ai_lab`, host in `databricks.yml`), catalog `erp_farma`. The initial 3-year backfill ran successfully end to end and `tests/conferencia.sql` passed. The dashboard deployed and its refresh task succeeds, but its widgets have not been checked visually yet.

The Genie space "Farma - Assistente Comercial" exists and is created/updated from the files in `genie/`:

```bash
uv run python genie/montar_space.py <warehouse_id> > genie/space.json
databricks genie create-space --json @genie/space.json            # first time
databricks genie update-space <space_id> --json @genie/space.json # after editing genie/*
```

When a Genie answer is wrong, fix it by adding a rule to the "Instruções gerais" block in `genie/instrucoes.md` or a reference query to `genie/consultas_exemplo.sql`, then update the space. Genie can be queried programmatically through the Conversation API (`/api/2.0/genie/spaces/{space_id}/start-conversation`).
