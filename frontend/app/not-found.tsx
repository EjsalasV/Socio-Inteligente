import Link from "next/link";

export default function NotFoundPage() {
  return (
    <main className="min-h-screen bg-[#f4f7f8] text-[#041627] flex items-center justify-center px-6">
      <section className="max-w-xl w-full rounded-editorial border border-[#041627]/10 bg-white p-8 shadow-editorial">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500 font-semibold">404</p>
        <h1 className="font-headline text-4xl mt-2">Pagina no encontrada</h1>
        <p className="mt-3 text-sm text-slate-600">
          La ruta que abriste no existe o ya no esta disponible.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/clientes"
            className="px-4 py-2 rounded-xl bg-[#041627] text-white text-sm font-semibold hover:opacity-90"
          >
            Ir a Clientes
          </Link>
          <Link
            href="/"
            className="px-4 py-2 rounded-xl border border-[#041627]/20 text-[#041627] text-sm font-semibold hover:bg-[#f1f4f6]"
          >
            Ir al inicio
          </Link>
        </div>
      </section>
    </main>
  );
}
