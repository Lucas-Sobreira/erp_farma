import { memo } from "react";
import type { Indicador } from "../api";
import { useIndicadores } from "../hooks/useIndicadores";

function formatarValor({ valor, formato }: Indicador): string {
  if (valor == null) return "—";
  if (formato === "moeda") {
    // Valores grandes em notação compacta (R$ 1,09 mi) para caberem no cartão.
    const compacto = Math.abs(valor) >= 100_000;
    return valor.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      notation: compacto ? "compact" : "standard",
      maximumFractionDigits: 2,
    });
  }
  if (formato === "percentual") return `${valor.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
  return valor.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function Variacao({ indicador }: { indicador: Indicador }) {
  const { variacao, unidade_variacao } = indicador;
  if (variacao == null) return null;
  const estavel = Math.abs(variacao) < 0.05;
  const numero = Math.abs(variacao).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const unidade = unidade_variacao === "pp" ? " p.p." : "%";
  const sentido = estavel ? "estavel" : variacao > 0 ? "subiu" : "caiu";
  const descricao = estavel ? "estável" : `${variacao > 0 ? "alta" : "queda"} de ${numero}${unidade}`;
  return (
    <span className={`variacao variacao-${sentido}`} aria-label={`${descricao} em relação ao período anterior`}>
      <span aria-hidden>{estavel ? "=" : variacao > 0 ? "▲" : "▼"}</span> {numero}
      {unidade}
    </span>
  );
}

const Cartao = memo(function Cartao({ indicador }: { indicador: Indicador }) {
  return (
    <div className="indicador">
      <dt>{indicador.rotulo}</dt>
      <dd>
        <span className="indicador-valor">{formatarValor(indicador)}</span>
        <Variacao indicador={indicador} />
        {indicador.detalhe && <span className="indicador-detalhe">{indicador.detalhe}</span>}
      </dd>
    </div>
  );
});

const dataBr = (iso: string) => iso.split("-").reverse().join("/");

/** Faixa de KPIs acima da conversa. Sem dados e sem servidor, simplesmente não aparece. */
export function FaixaIndicadores() {
  const { indicadores, situacao } = useIndicadores();

  if (!indicadores) {
    if (situacao === "erro") return null;
    return (
      <section className="faixa-indicadores" aria-label="Indicadores" aria-busy>
        <div className="indicadores">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="indicador esqueleto" aria-hidden />
          ))}
        </div>
        <p className="nota">Calculando os indicadores. Na primeira vez o banco de dados pode levar alguns segundos para iniciar.</p>
      </section>
    );
  }

  return (
    <section className="faixa-indicadores" aria-label="Indicadores">
      <dl className="indicadores">
        {indicadores.indicadores.map((indicador) => (
          <Cartao key={indicador.id} indicador={indicador} />
        ))}
      </dl>
      <p className="nota">
        Últimos {indicadores.dias} dias com vendas, até {dataBr(indicadores.dados_ate)}, comparados aos {indicadores.dias} dias
        anteriores.
        {situacao === "verificando" && " Verificando se há carga nova."}
        {situacao === "erro" && " Não foi possível verificar se há carga nova; estes são os números da última visita."}
      </p>
    </section>
  );
}
