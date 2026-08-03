"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { clearLearningProgress, getLearningProgress, type LearningProgress } from "../../lib/api/user";
import { useLearningRole } from "../../lib/hooks/useLearningRole";

export default function LearningProgressPage() {
  const { roleLabel } = useLearningRole();
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    getLearningProgress().then(setProgress).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo cargar el progreso.")).finally(() => setLoading(false));
  }, []);

  const nextCompetency = useMemo(() => {
    if (!progress?.competencies.length) return null;
    return [...progress.competencies].sort((a, b) => a.progress_pct - b.progress_pct || a.practice_count - b.practice_count)[0];
  }, [progress]);

  async function removeProgress(): Promise<void> {
    if (!window.confirm("¿Eliminar tu progreso educativo? Esta acción no afecta clientes, auditorías ni preferencias.")) return;
    setClearing(true);
    try {
      await clearLearningProgress();
      setProgress(await getLearningProgress());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo eliminar el progreso.");
    } finally {
      setClearing(false);
    }
  }

  if (loading) return <main className="p-8 text-sm text-slate-500">Preparando tu progreso educativo…</main>;

  return (
    <main className="space-y-7 pb-10 pt-4">
      <header className="rounded-2xl bg-[#041627] p-8 text-white">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#89d3d4]">Desarrollo personal · {roleLabel}</p>
        <h1 className="mt-2 font-headline text-4xl">Tu progreso como auditor</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-200">Observa qué competencias has practicado con el mentor. Esto es una herramienta privada de aprendizaje, no una calificación de desempeño.</p>
      </header>
      {error ? <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> : null}
      <section className="grid gap-5 md:grid-cols-3">
        <article className="sovereign-card"><p className="text-xs uppercase tracking-[0.12em] text-slate-500">Prácticas realizadas</p><p className="mt-2 font-headline text-4xl">{progress?.total_practices ?? 0}</p></article>
        <article className="sovereign-card md:col-span-2"><p className="text-xs uppercase tracking-[0.12em] text-slate-500">Siguiente foco sugerido</p><p className="mt-2 font-headline text-2xl">{nextCompetency?.label ?? "Inicia una sesión de mentoría desde el balance"}</p><p className="mt-2 text-sm text-slate-500">{nextCompetency ? `${nextCompetency.practice_count} prácticas · avance orientativo ${nextCompetency.progress_pct}%` : "El progreso aparecerá después de responder al mentor."}</p></article>
      </section>
      <section className="sovereign-card">
        <h2 className="font-headline text-3xl">Competencias practicadas</h2>
        {progress?.competencies.length ? <div className="mt-5 space-y-5">{progress.competencies.map((item) => <div key={item.id}><div className="flex justify-between gap-4 text-sm"><span className="font-semibold">{item.label}</span><span className="text-slate-500">{item.practice_count} prácticas</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-[#177e82]" style={{ width: `${item.progress_pct}%` }} /></div><p className="mt-1 text-[11px] text-slate-500">Indicador educativo basado en avance de conversaciones; no representa una nota.</p></div>)}</div> : <div className="mt-5 rounded-xl border border-dashed border-black/15 p-6 text-sm text-slate-500">Todavía no hay prácticas registradas. Abre una cuenta en el Trial Balance y utiliza el botón Mentor.</div>}
      </section>
      <section className="grid gap-6 lg:grid-cols-2">
        <article className="sovereign-card"><h2 className="font-headline text-2xl">Recursos recurrentes</h2><div className="mt-4 flex flex-wrap gap-2">{progress?.frequent_resources.length ? progress.frequent_resources.map((item) => <span key={item.code} className="rounded-lg bg-slate-100 px-3 py-2 text-sm">{item.code} · {item.count}</span>) : <p className="text-sm text-slate-500">Sin recursos recomendados todavía.</p>}</div><div className="mt-5 flex gap-3"><Link href="/biblioteca" className="text-sm font-semibold text-[#177e82]">Ir a Biblioteca</Link><Link href="/procedimientos" className="text-sm font-semibold text-[#177e82]">Ver procedimientos</Link></div></article>
        <article className="rounded-2xl border border-[#89d3d4]/50 bg-[#edfafa] p-6"><h2 className="font-headline text-2xl text-[#041627]">Privacidad del aprendizaje</h2><p className="mt-3 text-sm leading-6 text-[#164e52]">{progress?.privacy}</p><p className="mt-2 text-xs text-slate-600">No se almacenan nombres de clientes, cuentas, saldos, respuestas textuales ni contenido generado por IA.</p><button type="button" disabled={clearing || !progress?.total_practices} onClick={() => void removeProgress()} className="mt-5 rounded-xl border border-red-200 bg-white px-4 py-2 text-xs font-semibold text-red-700 disabled:opacity-40">{clearing ? "Eliminando…" : "Eliminar mi progreso educativo"}</button></article>
      </section>
    </main>
  );
}
