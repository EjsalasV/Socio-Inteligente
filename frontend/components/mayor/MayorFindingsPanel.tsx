"use client";

import type { MayorValidaciones } from "../../types/mayor";

type Props = {
  validaciones: MayorValidaciones | null;
  isLoading?: boolean;
};

function ItemRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2 border-b border-black/5 last:border-b-0">
      <span className="text-sm text-slate-700">{label}</span>
      <span className="text-sm font-semibold text-[#041627]">{value}</span>
    </div>
  );
}

export default function MayorFindingsPanel({ validaciones, isLoading = false }: Props) {
  if (isLoading) {
    return <div className="sovereign-card h-28 animate-pulse bg-[#edf2f7]" />;
  }

  if (!validaciones) {
    return (
      <div className="sovereign-card">
        <h2 className="font-headline text-2xl text-[#041627]">Hallazgos</h2>
        <p className="text-sm text-slate-500 mt-2">No hay validaciones disponibles.</p>
      </div>
    );
  }

  return (
    <div className="sovereign-card">
      <h2 className="font-headline text-2xl text-[#041627]">Hallazgos Contables</h2>
      <p className="text-xs text-slate-500 mt-1">Generado: {validaciones.generated_at}</p>
      <div className="mt-4">
        <ItemRow
          label="Asientos descuadrados"
          value={`${validaciones.asientos_descuadrados.count_asientos} asientos / ${validaciones.asientos_descuadrados.count_movimientos} mov.`}
        />
        <ItemRow
          label="Líneas repetidas para validar"
          value={`${validaciones.duplicados.grupos} grupos / ${validaciones.duplicados.movimientos} mov.`}
        />
        {validaciones.duplicados.grupos > 0 ? (
          <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900">
            No son {validaciones.duplicados.grupos} errores confirmados. Son grupos con campos iguales; incluyen {validaciones.duplicados.movimientos_adicionales ?? 0} líneas adicionales que deben contrastarse con soporte o datos no incluidos en el mayor.
          </p>
        ) : null}
        <ItemRow
          label="Sin referencia"
          value={`${validaciones.movimientos_sin_referencia.count} mov.`}
        />
        <ItemRow
          label="Montos altos"
          value={`${validaciones.montos_altos.count} mov. (umbral ${Math.round(validaciones.montos_altos.threshold)})`}
        />
        <ItemRow
          label="Cerca de cierre"
          value={`${validaciones.movimientos_cerca_cierre.count} mov. en ${validaciones.movimientos_cerca_cierre.dias} días`}
        />
      </div>
    </div>
  );
}
