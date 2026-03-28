"use client";

import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { getPerfil } from "../../../lib/api/perfil";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";

const DOCUMENTS = [
  { name: "Escritura de constitucion", date: "12 Ene 2021", type: "description" },
  { name: "Contrato de prestamo LP", date: "05 Mar 2025", type: "contract" },
  { name: "Registro tributario", date: "22 Nov 2025", type: "badge" },
];

const FINDINGS = [
  {
    cycle: "Ciclo 2024",
    level: "MATERIAL",
    text: "Debilidad en conciliacion de partidas intercompanias.",
    state: "Remediado Q1-2025",
    tone: "error",
  },
  {
    cycle: "Ciclo 2023",
    level: "SIGNIFICATIVO",
    text: "Falta de soporte en gastos de representacion sobre umbral.",
    state: "Historico",
    tone: "primary",
  },
];

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

export default function ClientMemoryPage() {
  const { clienteId } = useAuditContext();
  const { data: dashboard, isLoading, error } = useDashboard(clienteId);

  const [perfilName, setPerfilName] = useState("");
  const [perfilSector, setPerfilSector] = useState("Holding");
  const [perfilMarco, setPerfilMarco] = useState("NIIF para PYMES");

  useEffect(() => {
    let active = true;
    async function loadPerfil(): Promise<void> {
      try {
        const perfil = await getPerfil(clienteId);
        if (!active) return;
        const root = (perfil?.perfil ?? {}) as Record<string, unknown>;
        const cliente = ((root.cliente as Record<string, unknown>) ?? {}) as Record<string, unknown>;
        const encargo = ((root.encargo as Record<string, unknown>) ?? {}) as Record<string, unknown>;

        setPerfilName(readString(cliente.nombre_legal, clienteId));
        setPerfilSector(readString(cliente.sector, "Holding"));
        setPerfilMarco(readString(encargo.marco_referencial, "NIIF para PYMES"));
      } catch {
        if (!active) return;
        setPerfilName(clienteId);
      }
    }

    if (clienteId) {
      void loadPerfil();
    }
    return () => {
      active = false;
    };
  }, [clienteId]);

  const topRisks = useMemo(() => dashboard?.top_areas?.slice(0, 3) ?? [], [dashboard]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!dashboard) return <ErrorMessage message="No hay contexto disponible para Client Memory." />;

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-[1500px]">
      <section className="space-y-2">
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Archivo permanente / Socio AI</p>
        <h1 className="font-headline text-5xl text-[#041627]">Memoria del Cliente</h1>
        <p className="font-headline italic text-xl text-slate-500">
          Expediente maestro de auditoria - <span className="text-[#041627] not-italic font-semibold">{perfilName || dashboard.nombre_cliente}</span>
        </p>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        <div className="xl:col-span-7 space-y-8">
          <article className="sovereign-card">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-headline text-3xl text-[#041627]">Perfil del Cliente</h3>
              <span className="px-3 py-1 rounded-full bg-teal-50 text-teal-700 text-[10px] font-bold uppercase tracking-[0.12em]">Activo</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-bold">Industria</p>
                <p className="text-lg font-medium text-slate-800 mt-1">{perfilSector}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-bold">Marco contable</p>
                <p className="text-lg font-medium text-slate-800 mt-1">{perfilMarco}</p>
              </div>
              <div className="md:col-span-2">
                <p className="text-[10px] uppercase tracking-[0.14em] text-slate-400 font-bold mb-2">Riesgos principales</p>
                <div className="flex flex-wrap gap-2">
                  {topRisks.map((risk) => (
                    <span key={risk.codigo} className="px-3 py-2 rounded-xl bg-[#f1f4f6] border-l-2 border-[#89d3d4] text-sm text-slate-700">
                      {risk.nombre}
                    </span>
                  ))}
                  {topRisks.length === 0 ? <span className="text-sm text-slate-500">Sin riesgos destacados.</span> : null}
                </div>
              </div>
            </div>
          </article>

          <article className="sovereign-card !p-0 overflow-hidden">
            <div className="p-6 border-b border-black/5 flex items-center justify-between">
              <h3 className="font-headline text-3xl text-[#041627]">Repositorio de Documentos</h3>
              <button className="text-xs uppercase tracking-[0.13em] font-bold text-teal-700">Cargar documento</button>
            </div>
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#f1f4f6]/70">
                  <th className="py-4 px-6 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Documento</th>
                  <th className="py-4 px-6 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Fecha</th>
                  <th className="py-4 px-6 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {DOCUMENTS.map((doc) => (
                  <tr key={doc.name} className="hover:bg-[#f8fbff]">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-teal-700 text-base">{doc.type}</span>
                        <span className="text-sm font-medium text-slate-800">{doc.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-500">{doc.date}</td>
                    <td className="py-4 px-6 text-right text-slate-400">
                      <button className="px-2"><span className="material-symbols-outlined text-base">visibility</span></button>
                      <button className="px-2"><span className="material-symbols-outlined text-base">edit</span></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </article>
        </div>

        <div className="xl:col-span-5 space-y-8">
          <article className="rounded-editorial p-8 relative overflow-hidden text-white" style={{ background: "linear-gradient(135deg, #1a2b3c 0%, #041627 100%)" }}>
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-5">
                <span className="material-symbols-outlined text-[#89d3d4]" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
                <h3 className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-bold">Memorandum estrategico AI</h3>
              </div>
              <h4 className="font-headline text-3xl">Cultura de control interno</h4>
              <p className="font-headline italic text-lg text-slate-200 mt-4 leading-relaxed">
                Se observan mejoras en segregacion de funciones. Aun se recomienda ampliar pruebas de recorrido en inventarios para cierre anual.
              </p>
              <div className="mt-6 pt-5 border-t border-white/10 flex items-center justify-between text-[10px] uppercase tracking-[0.12em] text-slate-300">
                <span>Socio AI</span>
                <span>Actualizado hoy</span>
              </div>
            </div>
            <div className="absolute -right-12 -bottom-12 w-44 h-44 rounded-full bg-[#89d3d4]/10 blur-3xl" />
          </article>

          <article className="sovereign-card">
            <h3 className="font-headline text-3xl text-[#041627] mb-6">Historial de Hallazgos</h3>
            <div className="space-y-5">
              {FINDINGS.map((f) => (
                <div key={f.cycle} className="relative pl-10">
                  <div className={`absolute left-0 top-1 w-6 h-6 rounded-full text-white flex items-center justify-center ${f.tone === "error" ? "bg-[#ba1a1a]" : "bg-[#041627]"}`}>
                    <span className="material-symbols-outlined text-sm">priority_high</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-slate-900">{f.cycle}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${f.tone === "error" ? "bg-[#ffdad6] text-[#93000a]" : "bg-[#d2e4fb] text-[#0b1d2d]"}`}>{f.level}</span>
                    </div>
                    <p className="text-sm text-slate-700">{f.text}</p>
                    <p className="text-[10px] uppercase tracking-[0.12em] text-slate-400 mt-1">{f.state}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-editorial overflow-hidden h-60 relative">
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCszSUQ4gyNuP-OPfC2qCaEmyvX06P2O9Q1uk8OcUbVB9t55_XhkRZt1maXKQTLXQdglzW0RR7Tb9jiWIs9inRHFTQkoKQTzOWbVoETrv7xxmx6ha2-uhLkzHACaePOIUxmcN4e_QpKzd7OqoGrHhw4XGhlCHWp2QYv77fBmur_kdwg4Nhah_ZZgMkobtRtptovshgtjyCZMGtM5iasXfhsXhADjmKrhNbggJpiIDBQit5OmGPAnH_ZWbHn8NjFTXtWKPuuuK56v7M"
              alt="Contexto arquitectonico"
              className="w-full h-full object-cover grayscale"
            />
            <div className="absolute inset-0 bg-[#041627]/25" />
            <p className="absolute bottom-5 left-5 right-5 font-headline italic text-white text-lg">
              "La integridad de los datos sostiene el criterio profesional."
            </p>
          </article>
        </div>
      </div>
    </div>
  );
}
