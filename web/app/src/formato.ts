import type { Coluna } from "./api";

const TIPOS_DECIMAIS = ["DECIMAL", "DOUBLE", "FLOAT"];
const TIPOS_INTEIROS = ["INT", "LONG", "BIGINT", "SHORT", "BYTE"];
// Colunas numéricas que são rótulos, não medidas: não levam separador de milhar nem barra.
const IDENTIFICADOR = /^(id_|ano$|mes$|dia$|trimestre$|lote|ean)/;

export function ehMedida(coluna: Coluna): boolean {
  return !IDENTIFICADOR.test(coluna.nome) && [...TIPOS_DECIMAIS, ...TIPOS_INTEIROS].includes(coluna.tipo);
}

export function formatarValor(valor: string | null, coluna: Coluna): string {
  if (valor == null) return "—";
  if (ehMedida(coluna)) {
    const casas = TIPOS_DECIMAIS.includes(coluna.tipo) ? 2 : 0;
    return Number(valor).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
  }
  if (coluna.tipo === "DATE" && /^\d{4}-\d{2}-\d{2}$/.test(valor)) return valor.split("-").reverse().join("/");
  return valor;
}

export function rotuloColuna(nome: string): string {
  const texto = nome.replaceAll("_", " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
