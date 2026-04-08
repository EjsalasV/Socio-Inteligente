"use client";

import { useLearningRole, type LearningRole } from "../../lib/hooks/useLearningRole";

type RoleDescriptions = Partial<Record<LearningRole, string>>;

type HelpItem = {
  label: string;
  description?: string;
  byRole?: RoleDescriptions;
};

type Props = {
  title: string;
  items: HelpItem[];
  compact?: boolean;
  defaultOpen?: boolean;
};

export default function ContextualHelp({ title, items, compact = false, defaultOpen = false }: Props) {
  const { role, roleLabel } = useLearningRole();

  function resolveRoleDescription(item: HelpItem): string {
    if (!item.byRole) return "";
    if (role === "socio") return (item.byRole.socio ?? item.byRole.senior ?? item.byRole.semi ?? "").trim();
    if (role === "senior") return (item.byRole.senior ?? item.byRole.semi ?? "").trim();
    if (role === "junior") return (item.byRole.junior ?? item.byRole.semi ?? "").trim();
    return (item.byRole.semi ?? "").trim();
  }

  function styleFallbackByRole(base: string): string {
    if (role === "junior") {
      return `Aprendizaje: ${base} Ejecuta en orden, deja evidencia minima y escala dudas al revisor.`;
    }
    if (role === "semi") {
      return `Ejecucion: ${base} Documenta criterio tecnico, evidencia y conclusion breve por area.`;
    }
    if (role === "senior") {
      return `Supervision: ${base} Valida materialidad, suficiencia de evidencia y consistencia del cierre tecnico.`;
    }
    return `Decision socio: ${base} Evalua impacto en opinion, riesgo residual y comunicacion final con la gerencia.`;
  }

  function getDescription(item: HelpItem): string {
    const byRole = resolveRoleDescription(item);
    if (byRole) return byRole;
    const base = (item.description ?? "").trim();
    if (!base) return "";
    return styleFallbackByRole(base);
  }

  return (
    <details
      open={defaultOpen}
      className={`rounded-xl border border-[#041627]/10 bg-white ${compact ? "p-3" : "p-4"}`}
    >
      <summary className="cursor-pointer list-none flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-[0.12em] text-slate-500 font-bold">{title}</span>
          <span className="px-2 py-0.5 rounded-full border border-[#041627]/20 bg-[#f8fafc] text-[10px] font-semibold text-slate-600">
            Nivel: {roleLabel}
          </span>
        </div>
        <span className="material-symbols-outlined text-slate-400 text-sm">help</span>
      </summary>
      <div className={`${compact ? "mt-3" : "mt-4"} space-y-2`}>
        {items.map((item) => (
          <div key={item.label} className="rounded-lg bg-[#f8fafc] border border-slate-200/70 px-3 py-2">
            <p className="text-xs font-semibold text-[#041627]">{item.label}</p>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">{getDescription(item)}</p>
          </div>
        ))}
      </div>
    </details>
  );
}
