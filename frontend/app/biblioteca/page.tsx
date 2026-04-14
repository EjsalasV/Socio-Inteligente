"use client";

import { useMemo, useState } from "react";

import { useLearningRole } from "../../lib/hooks/useLearningRole";
import { NORMAS, type NormaEntry } from "../../data/normas";

function categoriaLabel(categoria: NormaEntry["categoria"]): string {
  if (categoria === "NIIF_PYMES") return "NIIF PYMES";
  return categoria;
}

function faseLabel(fase: NormaEntry["cuando_aplica"]): string {
  if (fase === "planificacion") return "Planificación";
  if (fase === "ejecucion") return "Ejecución";
  if (fase === "informe") return "Informe";
  return "Todo el encargo";
}

export default function BibliotecaPage() {
  const { role, roleLabel } = useLearningRole();
  const [query, setQuery] = useState<string>("");
  const [selectedCodigo, setSelectedCodigo] = useState<string>(
    NORMAS.find((n) => n.categoria === "NIA")?.codigo ?? NORMAS[0]?.codigo ?? "",
  );
  const [mobileDetailOpen, setMobileDetailOpen] = useState<boolean>(false);

  const filteredNormas = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return NORMAS;
    return NORMAS.filter((norma) => {
      const hayTag = norma.tags.some((tag) => tag.toLowerCase().includes(q));
      return (
        norma.codigo.toLowerCase().includes(q) ||
        norma.titulo.toLowerCase().includes(q) ||
        hayTag
      );
    });
  }, [query]);

  const grouped = useMemo(() => {
    const categories: Array<NormaEntry["categoria"]> = ["NIA", "NIIF_PYMES", "NIC"];
    return categories.map((categoria) => ({
      categoria,
      items: filteredNormas.filter((n) => n.categoria === categoria),
    }));
  }, [filteredNormas]);

  const selectedNorma = useMemo(
    () => filteredNormas.find((n) => n.codigo === selectedCodigo) ?? filteredNormas[0] ?? null,
    [filteredNormas, selectedCodigo],
  );

  const rolePanelClass = useMemo(() => {
    if (role === "junior") return "bg-[#a5eff0]/15 border border-[#89d3d4] text-[#041627]";
    if (role === "semi") return "bg-slate-50 border border-slate-200 text-slate-700";
    if (role === "senior") return "bg-[#041627]/5 border border-[#041627]/20 text-[#041627]";
    return "bg-[#001919] text-white border border-[#89d3d4]/20";
  }, [role]);

  return (
    <div className="pt-4 pb-8 space-y-6 max-w-screen-2xl">
      <header className="sovereign-card">
        <p className="text-xs uppercase tracking-[0.16em] text-slate-500 font-semibold">Biblioteca</p>
        <h1 className="font-headline text-4xl text-[#041627] mt-2">Normas de Auditoría y Contabilidad</h1>
        <p className="text-sm text-slate-600 mt-2">
          Consulta rápida de NIAs y NIIF para PYMES con explicación adaptada por rol.
        </p>
      </header>

      <div className="md:hidden sovereign-card space-y-3">
        <label className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">
          Buscar norma
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ej: 315, inventarios, materialidad"
            className="mt-2 w-full rounded-lg border border-[#041627]/15 bg-[#f1f4f6] px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#89d3d4] focus:outline-none"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[320px_minmax(0,1fr)] gap-6">
        <aside className="hidden md:block sovereign-card max-h-[calc(100vh-180px)] overflow-auto">
          <label className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold block mb-3">
            Buscar norma
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ej: 315, inventarios, materialidad"
              className="mt-2 w-full rounded-lg border border-[#041627]/15 bg-[#f1f4f6] px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#89d3d4] focus:outline-none"
            />
          </label>

          <div className="space-y-5">
            {grouped.map((group) => (
              <div key={group.categoria}>
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold mb-2">
                  {categoriaLabel(group.categoria)}
                </p>
                <div className="space-y-2">
                  {group.items.length === 0 ? (
                    <p className="text-xs text-slate-400">Sin resultados en esta categoría.</p>
                  ) : (
                    group.items.map((norma) => (
                      <button
                        key={norma.codigo}
                        type="button"
                        onClick={() => setSelectedCodigo(norma.codigo)}
                        className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                          selectedNorma?.codigo === norma.codigo
                            ? "border-[#89d3d4] bg-[#a5eff0]/10"
                            : "border-black/10 bg-white hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="mt-0.5 rounded-full bg-[#041627]/10 px-2 py-0.5 text-[10px] font-bold text-[#041627]">
                            {norma.codigo}
                          </span>
                          <span className="text-xs text-slate-700 line-clamp-2">{norma.titulo}</span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        </aside>

        <section className="space-y-4">
          <div className="md:hidden sovereign-card space-y-3">
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Normas</p>
            <div className="space-y-2 max-h-80 overflow-auto">
              {filteredNormas.map((norma) => (
                <button
                  key={norma.codigo}
                  type="button"
                  onClick={() => {
                    setSelectedCodigo(norma.codigo);
                    setMobileDetailOpen(true);
                  }}
                  className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                    selectedNorma?.codigo === norma.codigo
                      ? "border-[#89d3d4] bg-[#a5eff0]/10"
                      : "border-black/10 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 rounded-full bg-[#041627]/10 px-2 py-0.5 text-[10px] font-bold text-[#041627]">
                      {norma.codigo}
                    </span>
                    <span className="text-xs text-slate-700">{norma.titulo}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {selectedNorma ? (
            <article className={`sovereign-card space-y-5 ${mobileDetailOpen ? "block" : "hidden"} md:block`}>
              <div className="md:hidden">
                {mobileDetailOpen ? (
                  <button
                    type="button"
                    onClick={() => setMobileDetailOpen(false)}
                    className="inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.1em] text-[#041627]"
                  >
                    <span className="material-symbols-outlined text-base">arrow_back</span>
                    Volver a la lista
                  </button>
                ) : null}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-[#041627] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-white">
                  {selectedNorma.codigo}
                </span>
                <span className="rounded-full border border-[#041627]/15 bg-[#f1f4f6] px-3 py-1 text-[11px] font-semibold text-[#041627]">
                  {faseLabel(selectedNorma.cuando_aplica)}
                </span>
                <span className="rounded-full border border-[#041627]/10 bg-white px-3 py-1 text-[11px] text-slate-600">
                  {categoriaLabel(selectedNorma.categoria)}
                </span>
              </div>

              <div>
                <h2 className="font-headline text-3xl text-[#041627]">{selectedNorma.titulo}</h2>
                <p className="text-sm text-slate-700 mt-3 leading-relaxed">{selectedNorma.objetivo}</p>
              </div>

              <div>
                <h3 className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Requisitos clave</h3>
                <ul className="list-disc pl-5 space-y-2 text-sm text-slate-700">
                  {selectedNorma.requisitos_clave.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className={`rounded-xl p-5 ${rolePanelClass}`}>
                <p className="text-[11px] uppercase tracking-[0.14em] font-bold mb-2">Vista por rol: {roleLabel}</p>
                <p className="text-sm leading-relaxed">{selectedNorma.vista[role]}</p>
              </div>
            </article>
          ) : (
            <article className="sovereign-card text-sm text-slate-600">
              Selecciona una norma para ver su detalle.
            </article>
          )}
        </section>
      </div>
    </div>
  );
}
