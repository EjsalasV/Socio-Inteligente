"use client";

import type { RiskMatrixCell } from "../../types/risk";

type Props = {
  cell: RiskMatrixCell;
};

export default function RiskTooltip({ cell }: Props) {
  const areaTitle = cell.area_nombre || `Zona ${cell.frecuencia}-${cell.impacto}`;

  return (
    <div className="risk-tooltip-animate absolute z-20 left-1/2 -translate-x-1/2 -top-3 -translate-y-full min-w-[220px] bg-[#041627] text-white rounded-xl p-3 shadow-[0_16px_34px_rgba(4,22,39,0.35)] pointer-events-none">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-headline text-lg leading-tight">{areaTitle}</h4>
        <span className="font-body text-[10px] uppercase tracking-[0.12em] bg-white/10 rounded px-2 py-1">{cell.nivel}</span>
      </div>

      <div className="mt-2 flex items-center justify-between text-xs font-body">
        <span className="text-white/75">Score</span>
        <span className="bg-white text-[#041627] rounded px-2 py-0.5 font-bold">{cell.score.toFixed(1)}</span>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-2 text-[11px] font-body">
        <div className="bg-white/10 rounded-lg px-2 py-1">
          <div className="uppercase tracking-[0.1em] text-white/65">Frecuencia</div>
          <div className="font-semibold mt-0.5">{cell.frecuencia}/5</div>
        </div>
        <div className="bg-white/10 rounded-lg px-2 py-1">
          <div className="uppercase tracking-[0.1em] text-white/65">Impacto</div>
          <div className="font-semibold mt-0.5">{cell.impacto}/5</div>
        </div>
      </div>
    </div>
  );
}
