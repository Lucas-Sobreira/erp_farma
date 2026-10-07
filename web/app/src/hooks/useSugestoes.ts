import { useEffect, useState } from "react";
import { buscarSugestoes } from "../api";

/** Perguntas sugeridas na tela inicial. Se a busca falhar, a tela simplesmente fica sem sugestões. */
export function useSugestoes() {
  const [sugestoes, setSugestoes] = useState<string[]>([]);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    const controle = new AbortController();
    buscarSugestoes(controle.signal)
      .then(setSugestoes)
      .catch(() => {})
      .finally(() => {
        if (!controle.signal.aborted) setCarregando(false);
      });
    return () => controle.abort();
  }, []);

  return { sugestoes, carregando };
}
