import { IconeEnviar } from "./Icones";

interface Props {
  sugestoes: string[];
  carregando: boolean;
  aoPerguntar: (pergunta: string) => void;
}

const ASSUNTOS = ["Faturamento e ticket médio", "Produtos e categorias", "Formas de pagamento", "Estoque e validade"];

export function BoasVindas({ sugestoes, carregando, aoPerguntar }: Props) {
  return (
    <section className="boas-vindas">
      <p className="sobretitulo">Assistente comercial</p>
      <h1>Pergunte aos dados da farmácia</h1>
      <p className="apresentacao">
        Escreva a pergunta como falaria com um analista. A resposta vem com os números que a sustentam e com a consulta
        usada para chegar neles.
      </p>
      <ul className="assuntos" aria-label="Assuntos disponíveis">
        {ASSUNTOS.map((assunto) => (
          <li key={assunto}>{assunto}</li>
        ))}
      </ul>

      <h2 className="rotulo">Comece por uma destas</h2>
      <div className="cartoes">
        {carregando
          ? Array.from({ length: 4 }, (_, i) => <div key={i} className="cartao esqueleto" aria-hidden />)
          : sugestoes.map((sugestao) => (
              <button key={sugestao} type="button" className="cartao" onClick={() => aoPerguntar(sugestao)}>
                <span>{sugestao}</span>
                <IconeEnviar />
              </button>
            ))}
      </div>
      <p className="nota">
        Os dados cobrem as vendas concluídas de todas as filiais e canais, atualizadas a cada carga do ERP. Não há dados
        pessoais de clientes.
      </p>
    </section>
  );
}
