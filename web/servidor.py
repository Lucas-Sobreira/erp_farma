"""Página do assistente comercial: serve o HTML e faz a ponte com o Genie.

O navegador nunca fala com o Databricks. Ele chama este servidor, que usa a
credencial do Databricks CLI (perfil OAuth) para chamar a Genie Conversation API.

Uso (na raiz do repositório):
  uv run --group web python web/servidor.py
  -> http://localhost:8000

Variáveis de ambiente opcionais:
  DATABRICKS_CONFIG_PROFILE  perfil do Databricks CLI (padrão: ai_lab)
  GENIE_SPACE_ID             id do Genie space (padrão: Farma - Assistente Comercial)
  PORT                       porta local (padrão: 8000)
"""

import json
import os
import re
import socket
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

PASTA = Path(__file__).parent
PERFIL = os.environ.get("DATABRICKS_CONFIG_PROFILE", "ai_lab")
SPACE_ID = os.environ.get("GENIE_SPACE_ID", "01f1c2742b961019bc2d55b20a284e1a")
PORTA = int(os.environ.get("PORT", "8000"))

TAMANHO_MAXIMO_PERGUNTA = 500
LINHAS_MAXIMAS = 100
ID_VALIDO = re.compile(r"^[0-9a-f]{32}$")
ESTADOS_FINAIS = {"COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"}

databricks = WorkspaceClient(profile=PERFIL)
BASE = f"/api/2.0/genie/spaces/{SPACE_ID}"


class RequisicaoInvalida(Exception):
    pass


def perguntas_sugeridas() -> list[str]:
    """As perguntas marcadas com ★ em genie/perguntas_exemplo.md."""
    markdown = (PASTA.parent / "genie" / "perguntas_exemplo.md").read_text(encoding="utf-8")
    return re.findall(r"^(?:\d+\.|-) ★ (.+)", markdown, re.M)


def perguntar(pergunta: str, conversa_id: str | None) -> dict:
    pergunta = (pergunta or "").strip()
    if not pergunta or len(pergunta) > TAMANHO_MAXIMO_PERGUNTA:
        raise RequisicaoInvalida(f"A pergunta deve ter entre 1 e {TAMANHO_MAXIMO_PERGUNTA} caracteres.")
    if conversa_id:
        _validar_id(conversa_id)
        r = databricks.api_client.do("POST", f"{BASE}/conversations/{conversa_id}/messages", body={"content": pergunta})
        return {"conversa_id": conversa_id, "mensagem_id": r["message_id"]}
    r = databricks.api_client.do("POST", f"{BASE}/start-conversation", body={"content": pergunta})
    return {"conversa_id": r["conversation_id"], "mensagem_id": r["message_id"]}


def resposta(conversa_id: str, mensagem_id: str) -> dict:
    _validar_id(conversa_id)
    _validar_id(mensagem_id)
    caminho = f"{BASE}/conversations/{conversa_id}/messages/{mensagem_id}"
    mensagem = databricks.api_client.do("GET", caminho)
    estado = mensagem["status"]
    if estado not in ESTADOS_FINAIS:
        return {"estado": estado, "pronto": False}

    saida = {"estado": estado, "pronto": True, "texto": None, "sql": None, "tabela": None, "sugestoes": []}
    if estado != "COMPLETED":
        saida["texto"] = (mensagem.get("error") or {}).get("error") or "Não foi possível responder a esta pergunta."
        return saida

    for anexo in mensagem.get("attachments") or []:
        if anexo.get("text"):
            saida["texto"] = anexo["text"].get("content")
        if anexo.get("suggested_questions"):
            saida["sugestoes"] = anexo["suggested_questions"].get("questions", [])
        if anexo.get("query"):
            saida["sql"] = anexo["query"].get("query")
            saida["texto"] = saida["texto"] or anexo["query"].get("description")
            saida["tabela"] = _resultado(f"{caminho}/attachments/{anexo['attachment_id']}/query-result")
    return saida


def _resultado(caminho: str) -> dict | None:
    try:
        r = databricks.api_client.do("GET", caminho)["statement_response"]
    except DatabricksError:
        return None
    colunas = [{"nome": c["name"], "tipo": c.get("type_name", "STRING")} for c in r["manifest"]["schema"]["columns"]]
    linhas = (r.get("result") or {}).get("data_array") or []
    return {"colunas": colunas, "linhas": linhas[:LINHAS_MAXIMAS], "total_linhas": len(linhas)}


def _validar_id(valor: str) -> None:
    if not ID_VALIDO.match(valor or ""):
        raise RequisicaoInvalida("Identificador inválido.")


class Manipulador(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self._enviar(HTTPStatus.OK, (PASTA / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif url.path == "/api/sugestoes":
            self._json(lambda: {"perguntas": perguntas_sugeridas()})
        elif url.path == "/api/resposta":
            q = parse_qs(url.query)
            self._json(lambda: resposta(q.get("conversa_id", [""])[0], q.get("mensagem_id", [""])[0]))
        else:
            self._enviar_json(HTTPStatus.NOT_FOUND, {"erro": "Não encontrado."})

    def do_POST(self):
        if urlparse(self.path).path != "/api/perguntar":
            self._enviar_json(HTTPStatus.NOT_FOUND, {"erro": "Não encontrado."})
            return
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 10_000:
            self._enviar_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"erro": "Requisição grande demais."})
            return
        try:
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            self._enviar_json(HTTPStatus.BAD_REQUEST, {"erro": "JSON inválido."})
            return
        self._json(lambda: perguntar(corpo.get("pergunta"), corpo.get("conversa_id")))

    def _json(self, funcao):
        try:
            self._enviar_json(HTTPStatus.OK, funcao())
        except RequisicaoInvalida as erro:
            self._enviar_json(HTTPStatus.BAD_REQUEST, {"erro": str(erro)})
        except DatabricksError as erro:
            # O detalhe fica no log do servidor; o navegador recebe uma mensagem genérica.
            self.log_error("Erro do Databricks: %s", erro)
            self._enviar_json(HTTPStatus.BAD_GATEWAY, {"erro": "O assistente está indisponível no momento."})

    def _enviar_json(self, status, dados):
        self._enviar(status, json.dumps(dados, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _enviar(self, status, corpo: bytes, tipo: str):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)


class ServidorIPv6(ThreadingHTTPServer):
    address_family = socket.AF_INET6


if __name__ == "__main__":
    # Só aceita conexões desta máquina: a página expõe dados comerciais sem login.
    # `localhost` pode resolver para IPv4 ou IPv6, então escuta nos dois loopbacks.
    print(f"Assistente Farma em http://localhost:{PORTA} (perfil {PERFIL}, space {SPACE_ID})", flush=True)
    try:
        ipv6 = ServidorIPv6(("::1", PORTA), Manipulador)
        threading.Thread(target=ipv6.serve_forever, daemon=True).start()
    except OSError:
        pass  # máquina sem IPv6
    ThreadingHTTPServer(("127.0.0.1", PORTA), Manipulador).serve_forever()
