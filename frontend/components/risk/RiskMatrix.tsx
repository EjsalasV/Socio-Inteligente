"use client";

import { useMemo, useState } from "react";

import RiskTooltip from "./RiskTooltip";
import type { RiskEngineResponse, RiskMatrixCell } from "../../types/risk";

type Props = {
  data: RiskEngineResponse;
  targetId?: string;
};

function bgClass(score: number): string {
  if (score >= 85) return "bg-[#b91c1c]";
  if (score >= 75) return "bg-[#dc2626]";
  if (score >= 65) return "bg-[#f97316]";
  if (score >= 55) return "bg-[#fb923c]";
  if (score >= 45) return "bg-[#facc15]";
  if (score >= 35) return "bg-[#34d399]";
  if (score >= 25) return "bg-[#22c55e]";
  return "bg-[#15803d]";
}

function canJump(cell: RiskMatrixCell): boolean {
  return cell.score >= 75;
}

export default function RiskMatrix({ data, targetId = "riesgos-criticos" }: Props) {
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const flatCells = useMemo(() => data.quadrants.flat(), [data.quadrants]);

  const handleJump = (): void => {
    if (typeof document === "undefined") return;
    const target = document.getElementById(targetId);
    if (!target) return;
    const offset = 104;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: "smooth" });
  };

  return (
    <section className="col-span-12 lg:col-span-7 bg-white p-8 rounded-xl shadow-sm">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h2 className="font-headline text-2xl text-[#041627] font-semibold">Matriz de Riesgo</h2>
          <p className="text-slate-500 text-sm mt-1">Riesgo inherente vs riesgo de control</p>
        </div>
        <div className="flex space-x-2">
          <div className="flex items-center space-x-1 px-2 py-1 bg-[#ffdad6] text-[#ba1a1a] text-[10px] font-bold rounded">ALTO</div>
          <div className="flex items-center space-x-1 px-2 py-1 bg-[#ebeef0] text-slate-500 text-[10px] font-bold rounded">BAJO</div>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="flex flex-col justify-between py-8 text-[10px] font-bold text-slate-400 tracking-widest uppercase [writing-mode:vertical-lr] rotate-180">
          Riesgo Inherente
        </div>

        <div className="flex-1">
          <div className="grid grid-cols-5 gap-1.5 md:gap-2 w-full aspect-square md:aspect-video lg:aspect-square">
            {flatCells.map((cell) => {
              const key = `${cell.row}-${cell.col}`;
              const clickable = canJump(cell);
              return (
                <button
                  key={key}
                  type="button"
                  onClick={clickable ? handleJump : undefined}
                  onMouseEnter={() => setHoveredKey(key)}
                  onMouseLeave={() => setHoveredKey((curr) => (curr === key ? null : curr))}
                  className={`relative rounded-sm transition-all ${bgClass(cell.score)} ${clickable ? "cursor-pointer hover:brightness-105" : "cursor-default"}`}
                  aria-label={`Frecuencia ${cell.frecuencia}, impacto ${cell.impacto}, score ${cell.score}`}
                >
                  {cell.area_id ? <div className="w-2 h-2 bg-white/80 rounded-full absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" /> : null}
                  {hoveredKey === key ? <RiskTooltip cell={cell} /> : null}
                </button>
              );
            })}
          </div>

          <div className="mt-4 flex justify-between text-[10px] font-bold text-slate-400 tracking-widest uppercase">
            <span>Bajo</span>
            <span>Riesgo de Control</span>
            <span>Alto</span>
          </div>
        </div>
      </div>
    </section>
  );
}
