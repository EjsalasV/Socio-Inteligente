"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import {
  getClienteDocumentos,
  getClienteHallazgos,
  uploadClienteDocumento,
  type ClienteDocumento,
} from "../../../lib/api/clientes";
import { getPerfil } from "../../../lib/api/perfil";
import { getExecutiveMemo } from "../../../lib/api/reportes";
import { buildApiUrl } from "../../../lib/api-base";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function formatDate(input: string): string {
  if (!input) return "Sin fecha";
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return input;
  return d.toLocaleDateString("es-EC", { year: "numeric", month: "short", day: "2-digit" });
}

export default function ClientMemoryPage() {
  const { clienteId } = useAuditContext();
  const { data: dashboard, isLoading, error } = useDashboard(clienteId);

  const [perfilName, setPerfilName] = useState("");
  const [perfilSector, setPerfilSector] = useState("Holding");
  const [perfilMarco, setPerfilMarco] = useState("NIIF para PYMES");
  const [memoText, setMemoText] = useState("");
  const [documentos, setDocumentos] = useState<ClienteDocumento[]>([]);
  const [hallazgos, setHallazgos] = useState<Array<{ title: string; body: string }>>([]);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    let active = true;
    async function loadPerfil(): Promise<void> {
      try {
        const [perfil, docs, findings, memo] = await Promise.all([
          getPerfil(clienteId),
          getClienteDocumentos(clienteId),
          getClienteHallazgos(clienteId),
          getExecutiveMemo(clienteId),
        ]);
        if (!active) return;
        const root = (perfil?.perfil ?? {}) as Record<string, unknown>;
        const cliente = ((root.cliente as Record<string, unknown>) ?? {}) as Record<string, unknown>;
        const encargo = ((root.encargo as Record<string, unknown>) ?? {}) as Record<string, unknown>;

        setPerfilName(readString(cliente.nombre_legal, clienteId));
        setPerfilSector(readString(cliente.sector, "Holding"));
        setPerfilMarco(readString(encargo.marco_referencial, "NIIF para PYMES"));
        setDocumentos(docs);
        setHallazgos(findings);
        setMemoText(memo.memo || "");
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
  const fileHelpText = "PDF/TXT se abren en nueva pestana. XLSX/CSV normalmente se descargan para revision.";

  async function handleUploadDocument(file: File): Promise<void> {
    setUploadingDoc(true);
    setUploadMsg("");
    try {
      const result = await uploadClienteDocumento(clienteId, file);
      setDocumentos(result.documentos);
      setUploadMsg(
        result.ingestion.indexed
          ? `Documento indexado para AI (${result.ingestion.text_chars} caracteres).`
          : "Documento cargado. No se pudo extraer texto util para AI.",
      );
    } catch (error) {
      setUploadMsg(error instanceof Error ? error.message : "No se pudo cargar el documento.");
    } finally {
      setUploadingDoc(false);
    }
  }

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
              <button
                type="button"
                className="text-xs uppercase tracking-[0.13em] font-bold text-teal-700 disabled:opacity-60"
                disabled={uploadingDoc}
                onClick={() => fileInputRef.current?.click()}
              >
                {uploadingDoc ? "Cargando..." : "Cargar documento"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleUploadDocument(file);
                  e.currentTarget.value = "";
                }}
              />
            </div>
            <div className="px-6 py-2 bg-[#f8fbff] border-b border-black/5 text-[11px] text-slate-500">{fileHelpText}</div>
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#f1f4f6]/70">
                  <th className="py-4 px-6 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Documento</th>
                  <th className="py-4 px-6 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Fecha</th>
                  <th className="py-4 px-6 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {documentos.map((doc) => (
                  <tr key={doc.id} className="hover:bg-[#f8fbff]">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-teal-700 text-base">description</span>
                        <span className="text-sm font-medium text-slate-800">{doc.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-500">{formatDate(doc.uploaded_at)}</td>
                    <td className="py-4 px-6 text-right text-slate-400">
                      <button
                        className="px-2"
                        type="button"
                        title="Abrir o descargar documento"
                        onClick={() =>
                          window.open(
                            buildApiUrl(`/clientes/${clienteId}/documentos/file?name=${encodeURIComponent(doc.name)}`),
                            "_blank",
                          )
                        }
                      >
                        <span className="material-symbols-outlined text-base">visibility</span>
                      </button>
                    </td>
                  </tr>
                ))}
                {documentos.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="py-6 px-6 text-sm text-slate-500">No hay documentos cargados.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
            {uploadMsg ? <div className="px-6 py-3 text-xs text-slate-600 border-t border-black/5">{uploadMsg}</div> : null}
          </article>
        </div>

        <div className="xl:col-span-5 space-y-8">
          <article className="rounded-editorial p-8 relative overflow-hidden text-white" style={{ background: "linear-gradient(135deg, #1a2b3c 0%, #041627 100%)" }}>
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-5">
                <span className="material-symbols-outlined text-[#89d3d4]" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
                <h3 className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-bold">Resumen Ejecutivo (AI + criterio auditor)</h3>
              </div>
              <h4 className="font-headline text-3xl">Memoria estrategica del cliente</h4>
              <p className="font-headline italic text-lg text-slate-200 mt-4 leading-relaxed whitespace-pre-wrap">
                {memoText || "Aun no hay resumen ejecutivo generado. Puedes crearlo desde la pestana Reportes con el boton 'Generar memo ejecutivo'."}
              </p>
              <div className="mt-6 pt-5 border-t border-white/10 flex items-center justify-between text-[10px] uppercase tracking-[0.12em] text-slate-300">
                <span>Socio AI</span>
                <span>{memoText ? "Resumen disponible" : "Pendiente de generar"}</span>
              </div>
            </div>
            <div className="absolute -right-12 -bottom-12 w-44 h-44 rounded-full bg-[#89d3d4]/10 blur-3xl" />
          </article>

          <article className="sovereign-card">
            <h3 className="font-headline text-3xl text-[#041627] mb-6">Historial de Hallazgos</h3>
            <div className="space-y-5">
              {hallazgos.map((f) => (
                <div key={`${f.title}-${f.body.slice(0, 24)}`} className="relative pl-10">
                  <div className="absolute left-0 top-1 w-6 h-6 rounded-full text-white flex items-center justify-center bg-[#041627]">
                    <span className="material-symbols-outlined text-sm">priority_high</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-slate-900">{f.title}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#d2e4fb] text-[#0b1d2d]">REGISTRO</span>
                    </div>
                    <p className="text-sm text-slate-700">{f.body || "Sin detalle."}</p>
                  </div>
                </div>
              ))}
              {hallazgos.length === 0 ? <p className="text-sm text-slate-500">No hay hallazgos registrados aun.</p> : null}
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

