import type { RiskCriticalArea } from "../../types/risk";

type Procedure = {
  nia: string;
  title: string;
  description: string;
  vinculo: string;
};

type Props = {
  areas: RiskCriticalArea[];
};

function buildProcedures(areas: RiskCriticalArea[]): Procedure[] {
  const joined = areas.map((a) => a.area_nombre.toLowerCase()).join(" ");

  const list: Procedure[] = [];
  if (joined.includes("ingreso") || joined.includes("cobrar") || joined.includes("venta")) {
    list.push({
      nia: "NIA 505",
      title: "Confirmación Externa de Saldos",
      description:
        "Solicitar confirmaciones directas de los principales saldos y validar diferencias con documentación soporte.",
      vinculo: "Ingresos / Cuentas por Cobrar",
    });
  }

  if (joined.includes("invent") || joined.includes("existenc")) {
    list.push({
      nia: "NIA 315",
      title: "Prueba de Recorrido (Walkthrough)",
      description:
        "Documentar el flujo completo de compras e inventario para evaluar diseño e implementación de controles clave.",
      vinculo: "Inventarios",
    });
  }

  if (joined.includes("efectivo") || joined.includes("banco") || joined.includes("tesorer")) {
    list.push({
      nia: "NIA 505",
      title: "Confirmaciones Bancarias y Conciliaciones",
      description:
        "Validar saldos de efectivo con confirmaciones externas y revisar partidas conciliatorias de cierre.",
      vinculo: "Efectivo",
    });
  }

  if (joined.includes("patrimonio") || joined.includes("inversion")) {
    list.push({
      nia: "NIA 540",
      title: "Revisión de Estimaciones y Valuaciones",
      description:
        "Evaluar supuestos de valuación, deterioro y revelaciones en patrimonio e inversiones no corrientes.",
      vinculo: "Patrimonio / Inversiones",
    });
  }

  list.push({
    nia: "NIA 520",
    title: "Procedimientos Analíticos Focalizados",
    description:
      "Contrastar tendencias por periodo y desviaciones no esperadas para identificar riesgo de incorrección material.",
    vinculo: "Análisis transversal",
  });

  const deduped: Procedure[] = [];
  const seen = new Set<string>();
  for (const p of list) {
    const key = `${p.nia}-${p.title}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(p);
  }
  return deduped.slice(0, 3);
}

export default function RiskProcedureSuggestions({ areas }: Props) {
  const procedures = buildProcedures(areas);

  return (
    <section className="col-span-12 lg:col-span-7 bg-[#f1f4f6] p-8 rounded-xl">
      <div className="flex items-center space-x-3 mb-8">
        <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-[#001919] text-[#a5eff0] text-xs font-bold" aria-hidden="true">
          AI
        </span>
        <h2 className="font-headline text-2xl text-[#041627] font-semibold">Socio AI - Sugerencia de Procedimientos</h2>
      </div>

      <div className="space-y-6">
        {procedures.map((procedure) => (
          <div key={`${procedure.nia}-${procedure.title}`} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200/50">
            <div className="flex justify-between items-start mb-4">
              <div className="bg-[#001919]/5 px-3 py-1 rounded-full border border-[#001919]/10">
                <span className="text-[#001919] font-bold text-xs uppercase tracking-wider">{procedure.nia}</span>
              </div>
              <button className="text-slate-400 hover:text-[#041627] transition-colors" type="button" aria-label="Agregar procedimiento">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-current text-sm">+</span>
              </button>
            </div>
            <h5 className="font-bold text-slate-900 mb-2">{procedure.title}</h5>
            <p className="text-sm text-slate-600 mb-4">{procedure.description}</p>
            <div className="flex items-center space-x-4 text-[10px] font-bold text-[#001919] uppercase tracking-widest">
              <span className="flex items-center">
                <span className="mr-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-[#001919] text-white text-[10px]">✓</span>
                Vinculado a: {procedure.vinculo}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
