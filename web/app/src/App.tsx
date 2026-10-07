import { useCallback, useEffect, useRef } from "react";
import { BoasVindas } from "./components/BoasVindas";
import { Compositor } from "./components/Compositor";
import { FaixaIndicadores } from "./components/FaixaIndicadores";
import { IconeCruz, IconeLua, IconeMais, IconeSol } from "./components/Icones";
import { Turno } from "./components/Turno";
import { useConversa } from "./hooks/useConversa";
import { useSugestoes } from "./hooks/useSugestoes";
import { useTema } from "./hooks/useTema";

export function App() {
  const { turnos, ocupado, perguntar, novaConversa } = useConversa();
  const { sugestoes, carregando } = useSugestoes();
  const [tema, alternarTema] = useTema();
  const campo = useRef<HTMLTextAreaElement>(null);
  const fim = useRef<HTMLDivElement>(null);

  // Acompanha a conversa: rola até o fim quando chega uma pergunta ou uma resposta.
  const situacaoDoUltimo = turnos.at(-1)?.situacao;
  useEffect(() => {
    if (!turnos.length) return;
    const suave = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    fim.current?.scrollIntoView({ behavior: suave ? "smooth" : "auto", block: "end" });
  }, [turnos.length, situacaoDoUltimo]);

  // Devolve o foco ao campo quando a resposta termina, para a próxima pergunta.
  useEffect(() => {
    if (!ocupado) campo.current?.focus();
  }, [ocupado]);

  const recomecar = useCallback(() => {
    novaConversa();
    campo.current?.focus();
  }, [novaConversa]);

  return (
    <div className="pagina">
      <header className="cabecalho">
        <div className="marca">
          <IconeCruz />
          <span>
            Farma <small>Área Comercial</small>
          </span>
        </div>
        <div className="acoes">
          {turnos.length > 0 && (
            <button type="button" className="botao botao-contorno" onClick={recomecar}>
              <IconeMais />
              <span>Nova conversa</span>
            </button>
          )}
          <button
            type="button"
            className="botao botao-icone"
            onClick={alternarTema}
            aria-label={tema === "claro" ? "Mudar para o tema escuro" : "Mudar para o tema claro"}
          >
            {tema === "claro" ? <IconeLua /> : <IconeSol />}
          </button>
        </div>
      </header>

      <main className="conteudo">
        <FaixaIndicadores />
        {turnos.length === 0 ? (
          <BoasVindas sugestoes={sugestoes} carregando={carregando} aoPerguntar={perguntar} />
        ) : (
          <div className="conversa" aria-live="polite">
            {turnos.map((turno, i) => (
              <Turno
                key={turno.id}
                turno={turno}
                ultimo={i === turnos.length - 1}
                ocupado={ocupado}
                aoPerguntar={perguntar}
              />
            ))}
          </div>
        )}
        <div ref={fim} />
      </main>

      <footer className="rodape">
        <Compositor ref={campo} ocupado={ocupado} aoPerguntar={perguntar} />
      </footer>
    </div>
  );
}
