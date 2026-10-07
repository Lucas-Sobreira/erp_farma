const ETAPAS = [
  { rotulo: "Entendendo a pergunta", estados: ["SUBMITTED", "FETCHING_METADATA", "FILTERING_CONTEXT"] },
  { rotulo: "Montando a consulta", estados: ["ASKING_AI"] },
  { rotulo: "Consultando os dados", estados: ["PENDING_WAREHOUSE", "EXECUTING_QUERY"] },
];

/** Mostra em que passo o Genie está, para a espera de 10 a 40 segundos não parecer travamento. */
export function Andamento({ etapa, novaTentativa }: { etapa: string; novaTentativa: boolean }) {
  const atual = Math.max(
    0,
    ETAPAS.findIndex((e) => e.estados.includes(etapa)),
  );
  return (
    <div className="andamento" role="status">
      <ol>
        {ETAPAS.map((e, i) => (
          <li key={e.rotulo} className={i < atual ? "feita" : i === atual ? "atual" : undefined}>
            <span className="marcador" aria-hidden />
            {e.rotulo}
            {i === atual && etapa === "PENDING_WAREHOUSE" ? " (o banco está iniciando)" : ""}
          </li>
        ))}
      </ol>
      {novaTentativa && <p className="nota">A primeira tentativa falhou no serviço do Genie. Tentando de novo.</p>}
    </div>
  );
}
