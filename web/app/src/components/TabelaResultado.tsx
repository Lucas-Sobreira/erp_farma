import { memo, useMemo, useState } from "react";
import type { Tabela } from "../api";
import { ehMedida, formatarValor, rotuloColuna } from "../formato";
import { IconeOrdem } from "./Icones";

interface Ordem {
  coluna: number;
  direcao: "asc" | "desc";
}

/** Tabela de resultados: ordena ao clicar no cabeçalho e mostra uma barra na primeira medida. */
export const TabelaResultado = memo(function TabelaResultado({ tabela }: { tabela: Tabela }) {
  const [ordem, setOrdem] = useState<Ordem | null>(null);
  const { colunas, linhas, total_linhas } = tabela;

  const medidas = useMemo(() => colunas.map(ehMedida), [colunas]);
  const colunaBarra = medidas.indexOf(true);
  const maximo = useMemo(
    () => (colunaBarra < 0 ? 0 : Math.max(0, ...linhas.map((linha) => Number(linha[colunaBarra]) || 0))),
    [linhas, colunaBarra],
  );

  const ordenadas = useMemo(() => {
    if (!ordem) return linhas;
    const sinal = ordem.direcao === "asc" ? 1 : -1;
    const numerica = medidas[ordem.coluna];
    // Copia antes de ordenar: sort altera o array original.
    return [...linhas].sort((a, b) => {
      const [x, y] = [a[ordem.coluna], b[ordem.coluna]];
      if (x == null || y == null) return x == null ? (y == null ? 0 : 1) : -1;
      return sinal * (numerica ? Number(x) - Number(y) : x.localeCompare(y, "pt-BR", { numeric: true }));
    });
  }, [linhas, ordem, medidas]);

  // Primeiro clique ordena (medidas do maior para o menor), o segundo inverte, o terceiro volta à ordem original.
  const alternarOrdem = (coluna: number) =>
    setOrdem((atual) => {
      const primeira = medidas[coluna] ? "desc" : "asc";
      if (atual?.coluna !== coluna) return { coluna, direcao: primeira };
      return atual.direcao === primeira ? { coluna, direcao: primeira === "desc" ? "asc" : "desc" } : null;
    });

  if (!linhas.length) return <p className="nota">A consulta não retornou linhas.</p>;

  return (
    <>
      <div className="tabela-rolagem" tabIndex={0} role="region" aria-label="Resultado da consulta">
        <table>
          <thead>
            <tr>
              {colunas.map((coluna, i) => {
                const direcao = ordem?.coluna === i ? ordem.direcao : null;
                return (
                  <th
                    key={coluna.nome}
                    className={medidas[i] ? "numero" : undefined}
                    aria-sort={direcao ? (direcao === "asc" ? "ascending" : "descending") : "none"}
                  >
                    <button type="button" className="ordenar" onClick={() => alternarOrdem(i)}>
                      {rotuloColuna(coluna.nome)}
                      <IconeOrdem direcao={direcao} />
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {ordenadas.map((linha, n) => (
              <tr key={n}>
                {linha.map((valor, i) => (
                  <td key={i} className={medidas[i] ? "numero" : undefined}>
                    {i === colunaBarra && maximo > 0 && linhas.length > 1 ? (
                      <span className="com-barra">
                        <span className="trilho" aria-hidden>
                          <span className="barra" style={{ width: `${(Math.max(0, Number(valor) || 0) / maximo) * 100}%` }} />
                        </span>
                        <span>{formatarValor(valor, colunas[i])}</span>
                      </span>
                    ) : (
                      formatarValor(valor, colunas[i])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="nota">
        {total_linhas > linhas.length
          ? `Mostrando ${linhas.length} de ${total_linhas.toLocaleString("pt-BR")} linhas.`
          : `${linhas.length} ${linhas.length === 1 ? "linha" : "linhas"}.`}{" "}
        Clique em um cabeçalho para ordenar.
      </p>
    </>
  );
});
