import { useEffect, useState } from "react";
import { buscarIndicadores, type Indicadores } from "../api";

const CHAVE = "farma.indicadores";

function lerGuardados(): Indicadores | null {
  try {
    const bruto = localStorage.getItem(CHAVE);
    return bruto ? (JSON.parse(bruto) as Indicadores) : null;
  } catch {
    return null;
  }
}

/**
 * Indicadores do topo da página. Mostra na hora os da última visita e pergunta ao
 * servidor se há carga nova; ele só manda números novos quando a versão dos dados mudou.
 */
export function useIndicadores() {
  const [indicadores, setIndicadores] = useState<Indicadores | null>(lerGuardados);
  const [situacao, setSituacao] = useState<"verificando" | "pronto" | "erro">("verificando");

  useEffect(() => {
    const controle = new AbortController();
    buscarIndicadores(lerGuardados()?.versao ?? null, controle.signal)
      .then((resposta) => {
        if (resposta.atualizado) {
          setIndicadores(resposta);
          try {
            localStorage.setItem(CHAVE, JSON.stringify(resposta));
          } catch {
            // sem armazenamento: os indicadores são buscados de novo na próxima visita
          }
        }
        setSituacao("pronto");
      })
      .catch((erro: Error) => {
        if (erro.name !== "AbortError") setSituacao("erro");
      });
    return () => controle.abort();
  }, []);

  return { indicadores, situacao };
}
