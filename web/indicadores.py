"""Indicadores (KPIs) do topo da página, calculados sobre a camada Gold.

Só consulta o SQL warehouse quando há dados novos. O sinal de "dados novos" é a
última atualização concluída do pipeline `farma_medalhao`, lida pela API de
pipelines (não liga o warehouse). Enquanto ela não muda:
  - o servidor reaproveita o resultado guardado em web/.cache_indicadores.json;
  - o navegador, que informa a versão que já tem, recebe só "sem novidades".
"""

import json
import os
import threading
import time
from datetime import UTC, date, datetime
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

CATALOGO = os.environ.get("FARMA_CATALOGO", "erp_farma")
SCHEMA_GOLD = os.environ.get("FARMA_SCHEMA_GOLD", "gold")
PIPELINE = os.environ.get("FARMA_PIPELINE", "farma_medalhao")
ARQUIVO_CACHE = Path(__file__).parent / ".cache_indicadores.json"
DIAS = 30

# Os dois períodos são relativos ao último dia com vendas, não a hoje: se as
# cargas pararem, os indicadores continuam comparando períodos completos.
CONSULTA = f"""
WITH referencia AS (
  SELECT max(data_venda) AS fim FROM fato_vendas
),
vendas AS (
  SELECT
    v.data_venda > r.fim - {DIAS} AS periodo_atual,
    sum(v.faturamento) AS faturamento,
    count(DISTINCT v.id_venda) AS vendas,
    sum(v.margem_bruta) AS margem
  FROM fato_vendas AS v CROSS JOIN referencia AS r
  WHERE v.data_venda > r.fim - {2 * DIAS}
  GROUP BY 1
),
estoque AS (
  SELECT sum(valor_estoque) AS em_risco
  FROM fato_estoque
  WHERE posicao_atual AND dias_para_vencer <= 60 AND quantidade_disponivel > 0
)
SELECT
  CAST(r.fim AS STRING) AS fim,
  CAST(max(CASE WHEN periodo_atual THEN faturamento END) AS DOUBLE) AS faturamento,
  CAST(max(CASE WHEN NOT periodo_atual THEN faturamento END) AS DOUBLE) AS faturamento_anterior,
  max(CASE WHEN periodo_atual THEN vendas END) AS vendas,
  max(CASE WHEN NOT periodo_atual THEN vendas END) AS vendas_anterior,
  CAST(max(CASE WHEN periodo_atual THEN margem END) AS DOUBLE) AS margem,
  CAST(max(CASE WHEN NOT periodo_atual THEN margem END) AS DOUBLE) AS margem_anterior,
  CAST(max(e.em_risco) AS DOUBLE) AS estoque_em_risco
FROM vendas CROSS JOIN referencia AS r CROSS JOIN estoque AS e
GROUP BY r.fim
"""


class Indicadores:
    def __init__(self, databricks: WorkspaceClient):
        self._databricks = databricks
        self._trava = threading.Lock()
        self._pipeline_id: str | None = None
        self._warehouse_id = os.environ.get("SQL_WAREHOUSE_ID")
        self._cache = self._ler_cache()

    def obter(self, versao_do_navegador: str | None) -> dict:
        """Devolve os indicadores, ou só `atualizado: False` se o navegador já tem a versão atual."""
        with self._trava:  # uma consulta por vez, mesmo com várias abas abertas
            versao = self._versao_dos_dados()
            if not self._cache or self._cache["versao"] != versao:
                self._cache = {"versao": versao, **self._calcular()}
                ARQUIVO_CACHE.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")
            if versao_do_navegador == versao:
                return {"versao": versao, "atualizado": False}
            return {**self._cache, "atualizado": True}

    def _versao_dos_dados(self) -> str:
        """Identificador da última carga concluída. Muda quando o pipeline processa dados novos."""
        try:
            if not self._pipeline_id:
                achados = self._databricks.pipelines.list_pipelines(filter=f"name LIKE '{PIPELINE}'")
                self._pipeline_id = next(iter(achados)).pipeline_id
            atualizacoes = self._databricks.pipelines.get(self._pipeline_id).latest_updates or []
            concluida = next(a for a in atualizacoes if a.state and a.state.value == "COMPLETED")
            return concluida.update_id
        except (DatabricksError, StopIteration):
            # Sem acesso ao pipeline: recalcula no máximo uma vez por dia.
            return f"dia-{date.today().isoformat()}"

    def _calcular(self) -> dict:
        linha = self._consultar(CONSULTA)
        fim, fat, fat_ant, vendas, vendas_ant, margem, margem_ant, em_risco = linha
        numero = lambda valor: float(valor) if valor is not None else None  # noqa: E731
        fat, fat_ant, vendas, vendas_ant = numero(fat), numero(fat_ant), numero(vendas), numero(vendas_ant)
        margem, margem_ant = numero(margem), numero(margem_ant)

        def dividir(a, b):
            return a / b if a is not None and b else None

        def variacao(atual, anterior):
            razao = dividir(atual, anterior)
            return None if razao is None else (razao - 1) * 100

        ticket, ticket_ant = dividir(fat, vendas), dividir(fat_ant, vendas_ant)
        margem_pct = None if dividir(margem, fat) is None else dividir(margem, fat) * 100
        margem_pct_ant = None if dividir(margem_ant, fat_ant) is None else dividir(margem_ant, fat_ant) * 100
        pontos = None if margem_pct is None or margem_pct_ant is None else margem_pct - margem_pct_ant

        def indicador(id_, rotulo, valor, formato, variacao_=None, unidade="%", detalhe=None):
            return {
                "id": id_,
                "rotulo": rotulo,
                "valor": valor,
                "formato": formato,
                "variacao": variacao_,
                "unidade_variacao": unidade,
                "detalhe": detalhe,
            }

        return {
            "dados_ate": fim,
            "dias": DIAS,
            "calculado_em": datetime.now(UTC).isoformat(timespec="seconds"),
            "indicadores": [
                indicador("faturamento", "Faturamento", fat, "moeda", variacao(fat, fat_ant)),
                indicador("vendas", "Vendas", vendas, "inteiro", variacao(vendas, vendas_ant)),
                indicador("ticket", "Ticket médio", ticket, "moeda", variacao(ticket, ticket_ant)),
                indicador("margem", "Margem bruta", margem_pct, "percentual", pontos, "pp"),
                indicador(
                    "estoque",
                    "Estoque em risco",
                    numero(em_risco) or 0.0,
                    "moeda",
                    detalhe="vencido ou a vencer em 60 dias",
                ),
            ],
        }

    def _consultar(self, sql: str) -> list:
        if not self._warehouse_id:
            self._warehouse_id = next(iter(self._databricks.warehouses.list())).id
        corpo = {
            "warehouse_id": self._warehouse_id,
            "statement": sql,
            "catalog": CATALOGO,
            "schema": SCHEMA_GOLD,
            "wait_timeout": "50s",
        }
        r = self._databricks.api_client.do("POST", "/api/2.0/sql/statements", body=corpo)
        limite = time.monotonic() + 120  # o warehouse pode estar parado e precisar iniciar
        while r["status"]["state"] in ("PENDING", "RUNNING") and time.monotonic() < limite:
            time.sleep(2)
            r = self._databricks.api_client.do("GET", f"/api/2.0/sql/statements/{r['statement_id']}")
        if r["status"]["state"] != "SUCCEEDED":
            raise DatabricksError(
                f"Consulta dos indicadores terminou em {r['status']['state']}: {r['status'].get('error')}"
            )
        linhas = (r.get("result") or {}).get("data_array") or []
        if not linhas:
            raise DatabricksError("A camada Gold ainda não tem vendas para calcular os indicadores.")
        return linhas[0]

    @staticmethod
    def _ler_cache() -> dict | None:
        try:
            return json.loads(ARQUIVO_CACHE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
