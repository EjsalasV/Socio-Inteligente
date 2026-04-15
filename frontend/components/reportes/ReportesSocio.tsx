"use client";

type Props = {
  finalReports: Array<{
    title: string;
    auditor: string;
    fecha: string;
    hallazgosCount: number;
    path: string;
    filename: string;
  }>;
  canEmitFinal: boolean;
  onEmitFinal: () => void;
  onDownload: (path: string, filename: string) => void;
};

function hallazgoTone(count: number): string {
  if (count >= 3) return "border-rose-200 bg-rose-50 text-rose-800";
  if (count >= 1) return "border-amber-200 bg-amber-50 text-amber-800";
  return "border-emerald-200 bg-emerald-50 text-emerald-800";
}

export default function ReportesSocio({
  finalReports,
  canEmitFinal,
  onEmitFinal,
  onDownload,
}: Props) {
  return (
    <section className="space-y-5">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Reportes Finales</h2>
        <p className="mt-2 text-sm text-slate-600">
          Vista ejecutiva para emisión y descarga de reportes listos para cliente.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onEmitFinal}
          disabled={!canEmitFinal}
          className="rounded-lg bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white disabled:opacity-60"
        >
          Autorizar y Emitir
        </button>
        <span className="inline-flex items-center rounded-lg border border-[#041627]/20 px-3 py-2 text-xs text-slate-600">
          {canEmitFinal ? "Estado de gates: listo para emisión" : "Estado de gates: pendiente de requisitos"}
        </span>
      </div>

      {finalReports.length === 0 ? (
        <article className="sovereign-card text-sm text-slate-600">
          Aún no hay reportes finalizados para este cliente.
        </article>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {finalReports.map((report) => (
            <article key={`${report.filename}-${report.fecha}`} className="sovereign-card">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-headline text-2xl text-[#041627]">{report.title}</h3>
                  <p className="mt-1 text-xs text-slate-600">Auditor: {report.auditor} · {report.fecha}</p>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] ${hallazgoTone(report.hallazgosCount)}`}>
                  Hallazgos: {report.hallazgosCount}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => onDownload(report.path, report.filename)}
                  className="rounded-lg border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
                >
                  Descargar PDF final
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
