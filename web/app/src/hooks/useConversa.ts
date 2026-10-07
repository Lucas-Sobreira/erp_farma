import { useCallback, useEffect, useReducer, useRef } from "react";
import { consultarResposta, enviarPergunta, type Resposta } from "../api";

export type Turno =
  | { id: number; pergunta: string; situacao: "carregando"; etapa: string; novaTentativa: boolean }
  | { id: number; pergunta: string; situacao: "pronto"; resposta: Resposta }
  | { id: number; pergunta: string; situacao: "erro"; mensagem: string };

type Acao =
  | { tipo: "PERGUNTAR"; id: number; pergunta: string }
  | { tipo: "ETAPA"; id: number; etapa: string; novaTentativa: boolean }
  | { tipo: "RESPONDER"; id: number; resposta: Resposta }
  | { tipo: "FALHAR"; id: number; mensagem: string }
  | { tipo: "LIMPAR" };

function redutor(turnos: Turno[], acao: Acao): Turno[] {
  switch (acao.tipo) {
    case "PERGUNTAR":
      return [...turnos, { id: acao.id, pergunta: acao.pergunta, situacao: "carregando", etapa: "SUBMITTED", novaTentativa: false }];
    case "ETAPA":
      return turnos.map((t) =>
        t.id === acao.id && t.situacao === "carregando" ? { ...t, etapa: acao.etapa, novaTentativa: acao.novaTentativa } : t,
      );
    case "RESPONDER":
      return turnos.map((t) => (t.id === acao.id ? { id: t.id, pergunta: t.pergunta, situacao: "pronto", resposta: acao.resposta } : t));
    case "FALHAR":
      return turnos.map((t) => (t.id === acao.id ? { id: t.id, pergunta: t.pergunta, situacao: "erro", mensagem: acao.mensagem } : t));
    case "LIMPAR":
      return [];
  }
}

const INTERVALO_MS = 1500;
const LIMITE_MS = 180_000;
const FALHA_GENERICA = "O assistente não conseguiu responder agora. Tente perguntar de novo.";

const esperar = (ms: number, sinal: AbortSignal) =>
  new Promise<void>((resolver, rejeitar) => {
    const temporizador = setTimeout(resolver, ms);
    sinal.addEventListener("abort", () => {
      clearTimeout(temporizador);
      rejeitar(new DOMException("Cancelado", "AbortError"));
    });
  });

/** Estado da conversa com o Genie: envia a pergunta, acompanha o andamento e guarda as respostas. */
export function useConversa() {
  const [turnos, despachar] = useReducer(redutor, []);
  const conversaId = useRef<string | null>(null);
  const proximoId = useRef(1);
  const cancelamento = useRef<AbortController | null>(null);

  useEffect(() => () => cancelamento.current?.abort(), []);

  const perguntar = useCallback(async (texto: string) => {
    const pergunta = texto.trim();
    if (!pergunta || cancelamento.current) return;
    const id = proximoId.current++;
    const controle = new AbortController();
    cancelamento.current = controle;
    despachar({ tipo: "PERGUNTAR", id, pergunta });

    const tentar = async (novaTentativa: boolean): Promise<Resposta> => {
      const inicio = Date.now();
      const ids = await enviarPergunta(pergunta, conversaId.current, controle.signal);
      conversaId.current = ids.conversa_id;
      for (;;) {
        await esperar(INTERVALO_MS, controle.signal);
        const r = await consultarResposta(ids, controle.signal);
        if (r.pronto) return r;
        despachar({ tipo: "ETAPA", id, etapa: r.estado, novaTentativa });
        if (Date.now() - inicio > LIMITE_MS) throw new Error("A resposta demorou demais. Tente de novo em instantes.");
      }
    };

    try {
      // O serviço de IA do Genie às vezes falha de forma passageira: uma nova tentativa costuma resolver.
      let resposta = await tentar(false);
      if (resposta.estado === "FAILED") {
        despachar({ tipo: "ETAPA", id, etapa: "SUBMITTED", novaTentativa: true });
        resposta = await tentar(true);
      }
      if (resposta.estado === "COMPLETED") despachar({ tipo: "RESPONDER", id, resposta });
      else despachar({ tipo: "FALHAR", id, mensagem: resposta.texto ?? FALHA_GENERICA });
    } catch (erro) {
      if ((erro as Error).name !== "AbortError") despachar({ tipo: "FALHAR", id, mensagem: (erro as Error).message || FALHA_GENERICA });
    } finally {
      if (cancelamento.current === controle) cancelamento.current = null;
    }
  }, []);

  const novaConversa = useCallback(() => {
    cancelamento.current?.abort();
    cancelamento.current = null;
    conversaId.current = null;
    despachar({ tipo: "LIMPAR" });
  }, []);

  const ocupado = turnos.some((t) => t.situacao === "carregando");
  return { turnos, ocupado, perguntar, novaConversa };
}
