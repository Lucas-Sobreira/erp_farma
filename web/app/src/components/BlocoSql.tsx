import { useEffect, useState } from "react";
import { IconeCerto, IconeCopiar } from "./Icones";

export function BlocoSql({ sql }: { sql: string }) {
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    if (!copiado) return;
    const temporizador = setTimeout(() => setCopiado(false), 2000);
    return () => clearTimeout(temporizador);
  }, [copiado]);

  const copiar = () => {
    navigator.clipboard.writeText(sql).then(
      () => setCopiado(true),
      () => {}, // sem permissão de área de transferência: o texto continua selecionável
    );
  };

  return (
    <div className="sql">
      <button type="button" className="botao botao-discreto copiar" onClick={copiar}>
        {copiado ? <IconeCerto /> : <IconeCopiar />}
        {copiado ? "Copiada" : "Copiar"}
      </button>
      <pre>{sql}</pre>
    </div>
  );
}
