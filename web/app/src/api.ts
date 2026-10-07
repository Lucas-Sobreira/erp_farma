// Contrato com web/servidor.py, que faz a ponte com a Genie Conversation API.

export interface Coluna {
  nome: string;
  tipo: string;
}

export interface Tabela {
  colunas: Coluna[];
  linhas: (string | null)[][];
  total_linhas: number;
}

export interface Resposta {
  estado: string;
  pronto: true;
  texto: string | null;
  sql: string | null;
  tabela: Tabela | null;
  sugestoes: string[];
}

interface EmAndamento {
  estado: string;
  pronto: false;
}

interface Identificadores {
  conversa_id: string;
  mensagem_id: string;
}

async function chamar<T>(url: string, opcoes?: RequestInit): Promise<T> {
  const resposta = await fetch(url, opcoes);
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(dados.erro ?? "Não foi possível falar com o servidor.");
  return dados as T;
}

export function buscarSugestoes(sinal?: AbortSignal): Promise<string[]> {
  return chamar<{ perguntas: string[] }>("/api/sugestoes", { signal: sinal }).then((d) => d.perguntas);
}

export function enviarPergunta(pergunta: string, conversaId: string | null, sinal?: AbortSignal) {
  return chamar<Identificadores>("/api/perguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pergunta, conversa_id: conversaId }),
    signal: sinal,
  });
}

export function consultarResposta(ids: Identificadores, sinal?: AbortSignal) {
  const parametros = new URLSearchParams({ conversa_id: ids.conversa_id, mensagem_id: ids.mensagem_id });
  return chamar<Resposta | EmAndamento>(`/api/resposta?${parametros}`, { signal: sinal });
}

export interface Indicador {
  id: string;
  rotulo: string;
  valor: number | null;
  formato: "moeda" | "inteiro" | "percentual";
  variacao: number | null;
  unidade_variacao: "%" | "pp";
  detalhe: string | null;
}

export interface Indicadores {
  versao: string;
  dados_ate: string;
  dias: number;
  calculado_em: string;
  indicadores: Indicador[];
}

/** Informa a versão que o navegador já tem; o servidor só devolve os números se houver carga nova. */
export function buscarIndicadores(versaoAtual: string | null, sinal?: AbortSignal) {
  const consulta = versaoAtual ? `?${new URLSearchParams({ versao: versaoAtual })}` : "";
  return chamar<(Indicadores & { atualizado: true }) | { versao: string; atualizado: false }>(`/api/indicadores${consulta}`, {
    signal: sinal,
  });
}
