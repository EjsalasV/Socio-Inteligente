"use client";

import { useEffect, useState } from "react";

import type { MayorMovimientosParams } from "../../types/mayor";

type Props = {
  value: MayorMovimientosParams;
  isLoading?: boolean;
  onApply: (next: MayorMovimientosParams) => void;
  onReset: () => void;
};

function numberOrUndefined(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed);
  return Number.isFinite(n) ? n : undefined;
}

export default function MayorFilters({ value, isLoading = false, onApply, onReset }: Props) {
  const [draft, setDraft] = useState<MayorMovimientosParams>(value);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  return (
    <section className="sovereign-card">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 className="font-headline text-2xl text-[#041627]">Filtros del Mayor</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-editorial px-3 py-2 text-xs uppercase tracking-[0.12em] font-bold text-slate-600 border border-[#041627]/15 hover:bg-[#f5f8fb] min-h-[44px] disabled:opacity-50"
            onClick={() => {
              onReset();
              setDraft({});
            }}
            disabled={isLoading}
          >
            Limpiar
          </button>
          <button
            type="button"
            className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-white bg-[#041627] hover:bg-[#163550] min-h-[44px] disabled:opacity-50"
            onClick={() => onApply({ ...draft, page: 1 })}
            disabled={isLoading}
          >
            Aplicar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Fecha desde</span>
          <input
            type="date"
            value={draft.fecha_desde || ""}
            onChange={(e) => setDraft((p) => ({ ...p, fecha_desde: e.target.value || undefined }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Fecha hasta</span>
          <input
            type="date"
            value={draft.fecha_hasta || ""}
            onChange={(e) => setDraft((p) => ({ ...p, fecha_hasta: e.target.value || undefined }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Cuenta</span>
          <input
            type="text"
            placeholder="Ej: 1105"
            value={draft.cuenta || ""}
            onChange={(e) => setDraft((p) => ({ ...p, cuenta: e.target.value || undefined }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">L/S</span>
          <input
            type="text"
            placeholder="Ej: 140"
            value={draft.ls || ""}
            onChange={(e) => setDraft((p) => ({ ...p, ls: e.target.value || undefined }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Referencia</span>
          <input
            type="text"
            placeholder="Ej: RC-001"
            value={draft.referencia || ""}
            onChange={(e) => setDraft((p) => ({ ...p, referencia: e.target.value || undefined }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Texto libre</span>
          <input
            type="text"
            placeholder="Descripción / cuenta / asiento"
            value={draft.texto || ""}
            onChange={(e) => setDraft((p) => ({ ...p, texto: e.target.value || undefined }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Monto mínimo</span>
          <input
            type="number"
            inputMode="decimal"
            placeholder="0"
            value={typeof draft.monto_min === "number" ? String(draft.monto_min) : ""}
            onChange={(e) => setDraft((p) => ({ ...p, monto_min: numberOrUndefined(e.target.value) }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Monto máximo</span>
          <input
            type="number"
            inputMode="decimal"
            placeholder="0"
            value={typeof draft.monto_max === "number" ? String(draft.monto_max) : ""}
            onChange={(e) => setDraft((p) => ({ ...p, monto_max: numberOrUndefined(e.target.value) }))}
            className="ghost-input w-full mt-1 min-h-[44px]"
          />
        </label>
      </div>
    </section>
  );
}

