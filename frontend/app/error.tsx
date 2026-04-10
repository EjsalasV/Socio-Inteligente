"use client";

import Link from "next/link";
import { useEffect } from "react";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error("App error boundary:", error);
  }, [error]);

  return (
    <main className="min-h-screen bg-[#f4f7f8] text-[#041627] flex items-center justify-center px-6">
      <section className="max-w-xl w-full rounded-editorial border border-[#041627]/10 bg-white p-8 shadow-editorial">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500 font-semibold">Error de modulo</p>
        <h1 className="font-headline text-4xl mt-2">No se pudo abrir el modulo</h1>
        <p className="mt-3 text-sm text-slate-600">
          Ocurrio un error inesperado en esta pantalla. Puedes reintentar sin perder sesion.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => reset()}
            className="px-4 py-2 rounded-xl bg-[#041627] text-white text-sm font-semibold hover:opacity-90"
          >
            Reintentar
          </button>
          <Link
            href="/clientes"
            className="px-4 py-2 rounded-xl border border-[#041627]/20 text-[#041627] text-sm font-semibold hover:bg-[#f1f4f6]"
          >
            Ir a Clientes
          </Link>
        </div>
      </section>
    </main>
  );
}
