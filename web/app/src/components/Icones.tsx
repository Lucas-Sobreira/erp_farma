import type { SVGProps } from "react";

const base: SVGProps<SVGSVGElement> = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export const IconeCruz = () => (
  <svg width="26" height="26" viewBox="0 0 22 22" aria-hidden>
    <path fill="currentColor" d="M8 1h6v7h7v6h-7v7H8v-7H1V8h7z" />
  </svg>
);
export const IconeEnviar = () => (
  <svg {...base}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);
export const IconeMais = () => (
  <svg {...base}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);
export const IconeSol = () => (
  <svg {...base}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
);
export const IconeLua = () => (
  <svg {...base}>
    <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
  </svg>
);
export const IconeCopiar = () => (
  <svg {...base}>
    <rect x="9" y="9" width="11" height="11" rx="2" />
    <path d="M5 15V6a2 2 0 0 1 2-2h9" />
  </svg>
);
export const IconeCerto = () => (
  <svg {...base}>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </svg>
);
export const IconeOrdem = ({ direcao }: { direcao: "asc" | "desc" | null }) => (
  <svg {...base} width={12} height={12}>
    <path d="M7 10l5-5 5 5" opacity={direcao === "desc" ? 0.25 : 1} />
    <path d="M7 14l5 5 5-5" opacity={direcao === "asc" ? 0.25 : 1} />
  </svg>
);
