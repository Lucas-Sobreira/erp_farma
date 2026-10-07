import { Component, type ErrorInfo, type ReactNode } from "react";

interface Estado {
  falhou: boolean;
}

/** Evita a tela em branco se algum componente quebrar ao renderizar uma resposta inesperada. */
export class LimiteDeErro extends Component<{ children: ReactNode }, Estado> {
  state: Estado = { falhou: false };

  static getDerivedStateFromError(): Estado {
    return { falhou: true };
  }

  componentDidCatch(erro: Error, info: ErrorInfo) {
    console.error("Falha ao renderizar a página:", erro, info);
  }

  render() {
    if (!this.state.falhou) return this.props.children;
    return (
      <div className="falha-geral" role="alert">
        <h1>A página encontrou um problema</h1>
        <p>Recarregue para começar uma nova conversa. Suas perguntas anteriores não foram perdidas no Genie.</p>
        <button className="botao botao-primario" type="button" onClick={() => window.location.reload()}>
          Recarregar a página
        </button>
      </div>
    );
  }
}
