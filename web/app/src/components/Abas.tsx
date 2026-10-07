import { createContext, useContext, useId, useState, type KeyboardEvent, type ReactNode } from "react";

interface ContextoAbas {
  ativa: string;
  ativar: (id: string) => void;
  prefixo: string;
}

const Contexto = createContext<ContextoAbas | undefined>(undefined);

function useAbas() {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("Componentes de aba devem ficar dentro de <Abas>.");
  return contexto;
}

/** Abas compostas: <Abas> guarda qual está ativa; <Aba> e <PainelAba> se ligam pelo id. */
export function Abas({ inicial, children }: { inicial: string; children: ReactNode }) {
  const [ativa, ativar] = useState(inicial);
  const prefixo = useId();
  return <Contexto.Provider value={{ ativa, ativar, prefixo }}>{children}</Contexto.Provider>;
}

export function ListaAbas({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  // Setas esquerda/direita movem entre as abas, como pede o padrão de tablist.
  const aoTeclar = (evento: KeyboardEvent<HTMLDivElement>) => {
    if (evento.key !== "ArrowRight" && evento.key !== "ArrowLeft") return;
    const abas = Array.from(evento.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
    const atual = abas.indexOf(document.activeElement as HTMLButtonElement);
    const proxima = abas[(atual + (evento.key === "ArrowRight" ? 1 : abas.length - 1)) % abas.length];
    proxima?.focus();
    proxima?.click();
  };
  return (
    <div className="abas" role="tablist" aria-label={rotulo} onKeyDown={aoTeclar}>
      {children}
    </div>
  );
}

export function Aba({ id, children }: { id: string; children: ReactNode }) {
  const { ativa, ativar, prefixo } = useAbas();
  const selecionada = ativa === id;
  return (
    <button
      type="button"
      role="tab"
      id={`${prefixo}-aba-${id}`}
      aria-selected={selecionada}
      aria-controls={`${prefixo}-painel-${id}`}
      tabIndex={selecionada ? 0 : -1}
      className="aba"
      onClick={() => ativar(id)}
    >
      {children}
    </button>
  );
}

export function PainelAba({ id, children }: { id: string; children: ReactNode }) {
  const { ativa, prefixo } = useAbas();
  if (ativa !== id) return null;
  return (
    <div role="tabpanel" id={`${prefixo}-painel-${id}`} aria-labelledby={`${prefixo}-aba-${id}`} className="painel-aba">
      {children}
    </div>
  );
}
