"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { getNormativaCatalogo } from "../../lib/api";
import { useLearningRole } from "../../lib/hooks/useLearningRole";
import type { NormaEntry } from "../../data/normas";

type CategoriaMap = Record<NormaEntry["categoria"], NormaEntry[]>;

const CATEGORIAS_ORDEN: Array<NormaEntry["categoria"]> = ["NIA", "NIIF_PYMES", "NIC", "NIIF"];

function isKnownCategoria(value: unknown): value is NormaEntry["categoria"] {
  return value === "NIA" || value === "NIIF_PYMES" || value === "NIC" || value === "NIIF";
}

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

function normalizeNormaToken(token: string | undefined | null): string {
  if (!token) return "";
  const trimmed = token.trim().toUpperCase();
  const nia = trimmed.match(/NIA\s*-?\s*(\d{3})/);
  if (nia) return `NIA-${nia[1]}`;
  const nic = trimmed.match(/NIC\s*-?\s*(\d+)/);
  if (nic) return `NIC-${nic[1]}`;
  const niifPymes = trimmed.match(/NIIF\s*PYMES\s*-?\s*(SECCION\s*)?(\d+)/);
  if (niifPymes) return `NIIF-PYMES-${niifPymes[2]}`;
  const niif = trimmed.match(/NIIF\s*-?\s*(\d+)/);
  if (niif) return `NIIF-${niif[1]}`;
  return trimmed;
}

export default function BibliotecaPage() {
  const { role, roleLabel } = useLearningRole();
  const searchParams = useSearchParams();

  const [loadingNormas, setLoadingNormas] = useState<boolean>(true);
  const [normas, setNormas] = useState<NormaEntry[]>([]);
  const [catalogMode, setCatalogMode] = useState<"integrated" | "static">("integrated");
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [queryInput, setQueryInput] = useState<string>("");
  const [debouncedQuery, setDebouncedQuery] = useState<string>("");
  const [selectedCodigo, setSelectedCodigo] = useState<string>("");
  const [mobileListOpen, setMobileListOpen] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    const run = async () => {
      try {
        const mod = await import("../../data/normas");
        const baseNormas = [...mod.NORMAS];
        let merged = baseNormas;

        try {
          const dynamicNormas = await getNormativaCatalogo();
          if (!active) return;
          const byCode = new Map<string, NormaEntry>();

          // Prioridad 1: catálogo dinámico construido desde data/conocimiento_normativo.
          for (const raw of dynamicNormas) {
            const codigo = normalizeNormaToken(String(raw.codigo || ""));
            if (!codigo) continue;
            if (!isKnownCategoria(raw.categoria)) continue;
            const fromApi: NormaEntry = {
              codigo,
              titulo: String(raw.titulo || codigo),
              categoria: raw.categoria,
              cuando_aplica: raw.cuando_aplica,
              objetivo: String(raw.objetivo || "Referencia normativa disponible para consulta."),
              requisitos_clave: Array.isArray(raw.requisitos_clave) ? raw.requisitos_clave.slice(0, 6) : [],
              tags: Array.isArray(raw.tags) ? raw.tags : [],
              vista: raw.vista,
            };
            byCode.set(codigo, fromApi);
          }

          // Prioridad 2: completar huecos con la biblioteca estática.
          for (const norma of baseNormas) {
            if (!byCode.has(norma.codigo)) {
              byCode.set(norma.codigo, norma);
            }
          }

          merged = Array.from(byCode.values()).sort((a, b) => {
            const catDelta = CATEGORIAS_ORDEN.indexOf(a.categoria) - CATEGORIAS_ORDEN.indexOf(b.categoria);
            if (catDelta !== 0) return catDelta;
            return a.codigo.localeCompare(b.codigo, "es");
          });
          if (active) setCatalogError(null);
        } catch (error) {
          if (active) {
            setCatalogMode("static");
            setCatalogError(
              error instanceof Error
                ? `Error al cargar catálogo dinámico: ${error.message}. Usando biblioteca local.`
                : "Error al cargar catálogo dinámico. Usando biblioteca local."
            );
          }
        }

        if (!active) return;
        setNormas(merged);
        const defaultNorma = merged.find((n) => n.categoria === "NIA") ?? merged[0];
        setSelectedCodigo((prev) => prev || defaultNorma?.codigo || "");
      } finally {
        if (active) setLoadingNormas(false);
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const rawNorma = String(searchParams.get("norma") || "").trim().toUpperCase();
    if (!rawNorma) return;
    const normalized = normalizeNormaToken(rawNorma);
    if (!normalized) return;
    setSelectedCodigo(normalized);
    setMobileListOpen(false);
  }, [searchParams]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedQuery(queryInput.trim().toLowerCase());
    }, 300);
    return () => window.clearTimeout(timeout);
  }, [queryInput]);

  const groupedBase = useMemo(() => {
    const grouped: CategoriaMap = { NIA: [], NIIF_PYMES: [], NIC: [], NIIF: [] };
    for (const norma of normas) {
      if (!grouped[norma.categoria]) continue;
      grouped[norma.categoria].push(norma);
    }
    return grouped;
  }, [normas]);

  const filteredGrouped = useMemo(() => {
    if (!debouncedQuery) return groupedBase;

    const next: CategoriaMap = { NIA: [], NIIF_PYMES: [], NIC: [], NIIF: [] };
    for (const categoria of CATEGORIAS_ORDEN) {
      next[categoria] = groupedBase[categoria].filter((norma) => {
        const inTags = norma.tags.some((tag) => tag.toLowerCase().includes(debouncedQuery));
        return (
          norma.codigo.toLowerCase().includes(debouncedQuery) ||
          norma.titulo.toLowerCase().includes(debouncedQuery) ||
          inTags
        );
      });
    }
    return next;
  }, [debouncedQuery, groupedBase]);

  const filteredFlat = useMemo(() => {
    return CATEGORIAS_ORDEN.flatMap((categoria) => filteredGrouped[categoria]);
  }, [filteredGrouped]);

  const selectedNorma = useMemo(() => {
    return filteredFlat.find((n) => n.codigo === selectedCodigo) ?? filteredFlat[0] ?? null;
  }, [filteredFlat, selectedCodigo]);

  useEffect(() => {
    if (!selectedNorma) return;
    if (selectedNorma.codigo !== selectedCodigo) {
      setSelectedCodigo(selectedNorma.codigo);
    }
  }, [selectedCodigo, selectedNorma]);

  const normaCodigoSet = useMemo(() => new Set(normas.map((n) => n.codigo)), [normas]);

  function renderLinkedText(text: string | undefined | null): React.ReactNode {
    if (!text) return null;
    const parts = text.split(/(NIIF\s*PYMES\s*-?\s*(SECCION\s*)?\d+|NIA\s*-?\s*\d{3}|NIC\s*-?\s*\d+|NIIF\s*-?\s*\d+)/gi);
    return parts.map((part, idx) => {
      if (!part) return null;
      const normalized = normalizeNormaToken(part);
      if (normalized && normaCodigoSet.has(normalized)) {
        return (
          <button
            key={`${part}-${idx}`}
            type="button"
            onClick={() => setSelectedCodigo(normalized)}
            className="font-semibold text-[#002f30] underline underline-offset-2 hover:text-[#041627]"
          >
            {part}
          </button>
        );
      }
      return <span key={`${part}-${idx}`}>{part}</span>;
    });
  }

  const rolePanelClass = useMemo(() => {
    if (role === "junior") return "bg-[#a5eff0]/15 border border-[#89d3d4] text-[#041627]";
    if (role === "semi") return "bg-white border border-[#89d3d4]/35 text-[#041627]";
    if (role === "senior") return "bg-[#041627]/5 border border-[#041627]/20 text-[#041627]";
    return "bg-[#041627] text-white border border-[#89d3d4]/25";
  }, [role]);

  return (
    <div className="pt-4 pb-8 space-y-6 max-w-screen-2xl">
      <header className="sovereign-card">
        <p className="text-xs uppercase tracking-[0.16em] text-slate-500 font-semibold">Biblioteca</p>
        <h1 className="font-headline text-4xl text-[#041627] mt-2">Normas de Auditoría y Contabilidad</h1>
        <p className="text-sm text-slate-600 mt-2">
          Consulta rápida de NIAs y NIIF para PYMES con explicación adaptada por rol.
        </p>
        {catalogError ? (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs text-amber-800">
              <span className="font-semibold">⚠️ Advertencia:</span> {catalogError}
            </p>
          </div>
        ) : null}
        {catalogMode === "static" && !catalogError ? (
          <p className="mt-2 text-xs text-slate-500">
            Modo local activo: mostrando biblioteca base sin sincronizacion dinamica.
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.12em] font-semibold">
          <span className={`rounded-full px-2.5 py-1 border ${role === "junior" ? "bg-[#89d3d4]/20 border-[#89d3d4] text-[#041627]" : "border-[#041627]/15 text-slate-500"}`}>Junior</span>
          <span className={`rounded-full px-2.5 py-1 border ${role === "semi" ? "bg-[#a5eff0]/20 border-[#89d3d4] text-[#041627]" : "border-[#041627]/15 text-slate-500"}`}>Semi</span>
          <span className={`rounded-full px-2.5 py-1 border ${role === "senior" ? "bg-[#041627]/10 border-[#041627]/30 text-[#041627]" : "border-[#041627]/15 text-slate-500"}`}>Senior</span>
          <span className={`rounded-full px-2.5 py-1 border ${role === "socio" ? "bg-[#041627] border-[#89d3d4]/35 text-[#89d3d4]" : "border-[#041627]/15 text-slate-500"}`}>Socio</span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-[320px_minmax(0,1fr)] gap-6">
        <aside className="sovereign-card md:max-h-[calc(100vh-180px)] md:overflow-auto">
          <div className="space-y-3">
            <label className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold block">
              Buscar norma
              <div className="mt-2 relative">
                <span className="material-symbols-outlined pointer-events-none absolute left-3 top-2.5 text-base text-slate-400">search</span>
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Busca por código, título o tag (ej: NIA 315, inventarios)"
                  className="w-full rounded-lg border border-[#041627]/15 bg-[#f1f4f6] pl-10 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#89d3d4] focus:outline-none"
                />
              </div>
            </label>

            <button
              type="button"
              onClick={() => setMobileListOpen((prev) => !prev)}
              className="md:hidden inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
            >
              <span className="material-symbols-outlined text-base">{mobileListOpen ? "expand_less" : "expand_more"}</span>
              {mobileListOpen ? "Ocultar listado" : "Mostrar listado"}
            </button>
          </div>

          <div className={`mt-4 space-y-5 ${mobileListOpen ? "block" : "hidden"} md:block`}>
            {loadingNormas ? (
              <p className="text-sm text-slate-500">Cargando biblioteca...</p>
            ) : (
              CATEGORIAS_ORDEN.map((categoria) => (
                <div key={categoria}>
                  <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold mb-2">
                    {categoriaLabel(categoria)}
                  </p>
                  <div className="space-y-2">
                    {filteredGrouped[categoria].length === 0 ? (
                      <p className="text-xs text-slate-400">Sin resultados en esta categoría.</p>
                    ) : (
                      filteredGrouped[categoria].map((norma) => (
                        <button
                          key={norma.codigo}
                          type="button"
                          onClick={() => {
                            setSelectedCodigo(norma.codigo);
                            setMobileListOpen(false);
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
                            <span className="text-xs text-slate-700 line-clamp-2">{norma.titulo}</span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        <section className="space-y-4">
          {selectedNorma ? (
            <article className="sovereign-card space-y-5">
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
                <p className="text-sm text-slate-700 mt-3 leading-relaxed">{renderLinkedText(selectedNorma.objetivo)}</p>
              </div>

              <div>
                <h3 className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Requisitos clave</h3>
                <ul className="list-disc pl-5 space-y-2 text-sm text-slate-700">
                  {selectedNorma.requisitos_clave.map((item) => (
                    <li key={item}>{renderLinkedText(item)}</li>
                  ))}
                </ul>
              </div>

              <div className={`rounded-xl p-5 ${rolePanelClass}`}>
                <p className="text-[11px] uppercase tracking-[0.14em] font-bold mb-2">Vista por rol: {roleLabel}</p>
                <p className="text-sm leading-relaxed">{renderLinkedText(selectedNorma.vista[role])}</p>
              </div>
            </article>
          ) : (
            <article className="sovereign-card text-sm text-slate-600">
              No hay normas para mostrar con el filtro actual.
            </article>
          )}
        </section>
      </div>
    </div>
  );
}
