import { Fragment, memo, type ReactNode } from "react";

function comNegrito(texto: string): ReactNode[] {
  return texto.split(/\*\*(.+?)\*\*/).map((trecho, i) => (i % 2 ? <strong key={i}>{trecho}</strong> : <Fragment key={i}>{trecho}</Fragment>));
}

/**
 * Renderiza o texto do Genie (parágrafos, listas com "- " e **negrito**) como elementos React.
 * Nunca usa HTML bruto: o conteúdo vem de um modelo e é tratado como texto.
 */
export const TextoGenie = memo(function TextoGenie({ texto }: { texto: string }) {
  const blocos: ReactNode[] = [];
  let itens: string[] = [];
  const fecharLista = () => {
    if (!itens.length) return;
    blocos.push(
      <ul key={blocos.length}>
        {itens.map((item, i) => (
          <li key={i}>{comNegrito(item)}</li>
        ))}
      </ul>,
    );
    itens = [];
  };
  for (const linha of texto.split("\n")) {
    const limpa = linha.trim();
    if (/^[-*] /.test(limpa)) {
      itens.push(limpa.slice(2));
      continue;
    }
    fecharLista();
    if (limpa) blocos.push(<p key={blocos.length}>{comNegrito(limpa)}</p>);
  }
  fecharLista();
  return <div className="texto-genie">{blocos}</div>;
});
