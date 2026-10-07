import { forwardRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { IconeEnviar } from "./Icones";

const LIMITE = 500;

interface Props {
  ocupado: boolean;
  aoPerguntar: (pergunta: string) => void;
}

/** Campo de pergunta fixo no rodapé. Enter envia; Shift+Enter quebra a linha. */
export const Compositor = forwardRef<HTMLTextAreaElement, Props>(function Compositor({ ocupado, aoPerguntar }, ref) {
  const [texto, setTexto] = useState("");
  const podeEnviar = !ocupado && texto.trim().length > 0;

  const enviar = () => {
    if (!podeEnviar) return;
    aoPerguntar(texto);
    setTexto("");
  };
  const aoSubmeter = (evento: FormEvent) => {
    evento.preventDefault();
    enviar();
  };
  const aoTeclar = (evento: KeyboardEvent<HTMLTextAreaElement>) => {
    if (evento.key === "Enter" && !evento.shiftKey && !evento.nativeEvent.isComposing) {
      evento.preventDefault();
      enviar();
    }
  };

  return (
    <form className="compositor" onSubmit={aoSubmeter}>
      <div className="campo">
        <label htmlFor="pergunta" className="somente-leitor">
          Sua pergunta
        </label>
        <textarea
          ref={ref}
          id="pergunta"
          rows={1}
          maxLength={LIMITE}
          value={texto}
          placeholder={ocupado ? "Aguarde a resposta em andamento" : "Ex.: qual filial mais vendeu genéricos este ano?"}
          onChange={(evento) => setTexto(evento.target.value)}
          onKeyDown={aoTeclar}
        />
        <button type="submit" className="botao botao-primario" disabled={!podeEnviar}>
          <span>Perguntar</span>
          <IconeEnviar />
        </button>
      </div>
      <p className="nota">
        Respostas geradas pelo Genie (Databricks) sobre a camada Gold. Confira os números antes de decidir.
        {texto.length > LIMITE - 100 && ` ${LIMITE - texto.length} caracteres restantes.`}
      </p>
    </form>
  );
});
