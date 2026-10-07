import { useCallback, useEffect, useState } from "react";

export type Tema = "claro" | "escuro";
const CHAVE = "farma.tema";

export function temaInicial(): Tema {
  try {
    const salvo = localStorage.getItem(CHAVE);
    if (salvo === "claro" || salvo === "escuro") return salvo;
  } catch {
    // armazenamento indisponível: segue o sistema
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
}

/** Tema da página: começa pelo do sistema e lembra a escolha de quem alternou. */
export function useTema(): [Tema, () => void] {
  const [tema, setTema] = useState<Tema>(temaInicial);

  useEffect(() => {
    document.documentElement.dataset.tema = tema;
  }, [tema]);

  const alternar = useCallback(() => {
    setTema((atual) => {
      const novo = atual === "claro" ? "escuro" : "claro";
      try {
        localStorage.setItem(CHAVE, novo);
      } catch {
        // sem armazenamento, a escolha vale só para esta visita
      }
      return novo;
    });
  }, []);

  return [tema, alternar];
}
