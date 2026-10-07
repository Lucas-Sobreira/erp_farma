import { memo } from "react";
import type { Resposta } from "../api";
import type { Turno as TurnoDaConversa } from "../hooks/useConversa";
import { Aba, Abas, ListaAbas, PainelAba } from "./Abas";
import { Andamento } from "./Andamento";
import { BlocoSql } from "./BlocoSql";
import { TabelaResultado } from "./TabelaResultado";
import { TextoGenie } from "./TextoGenie";

interface Props {
  turno: TurnoDaConversa;
  ultimo: boolean;
  ocupado: boolean;
  aoPerguntar: (pergunta: string) => void;
}

function RespostaPronta({ resposta }: { resposta: Resposta }) {
  const { texto, tabela, sql } = resposta;
  return (
    <>
      {texto && <TextoGenie texto={texto} />}
      {tabela && sql ? (
        <Abas inicial="dados">
          <ListaAbas rotulo="Detalhes da resposta">
            <Aba id="dados">Dados</Aba>
            <Aba id="sql">Consulta SQL</Aba>
          </ListaAbas>
          <PainelAba id="dados">
            <TabelaResultado tabela={tabela} />
          </PainelAba>
          <PainelAba id="sql">
            <BlocoSql sql={sql} />
          </PainelAba>
        </Abas>
      ) : (
        sql && <BlocoSql sql={sql} />
      )}
      {!texto && !tabela && !sql && <p>O assistente não retornou conteúdo para esta pergunta.</p>}
    </>
  );
}

export const Turno = memo(function Turno({ turno, ultimo, ocupado, aoPerguntar }: Props) {
  return (
    <article className="turno">
      <h2 className="pergunta">{turno.pergunta}</h2>
      <div
        className={`resposta${turno.situacao === "erro" ? " resposta-erro" : ""}`}
        aria-busy={turno.situacao === "carregando"}
      >
        {turno.situacao === "carregando" && <Andamento etapa={turno.etapa} novaTentativa={turno.novaTentativa} />}
        {turno.situacao === "pronto" && <RespostaPronta resposta={turno.resposta} />}
        {turno.situacao === "erro" && (
          <div role="alert" className="erro">
            <p>{turno.mensagem}</p>
            <button
              type="button"
              className="botao botao-contorno"
              disabled={ocupado}
              onClick={() => aoPerguntar(turno.pergunta)}
            >
              Perguntar de novo
            </button>
          </div>
        )}
      </div>
      {ultimo && turno.situacao === "pronto" && turno.resposta.sugestoes.length > 0 && (
        <div className="continuacoes">
          <span className="rotulo">Continue por aqui</span>
          {turno.resposta.sugestoes.slice(0, 3).map((sugestao) => (
            <button key={sugestao} type="button" className="chip" disabled={ocupado} onClick={() => aoPerguntar(sugestao)}>
              {sugestao}
            </button>
          ))}
        </div>
      )}
    </article>
  );
});
