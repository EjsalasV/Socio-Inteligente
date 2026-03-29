"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { createCliente, deleteCliente, getClientes, type ClienteOption } from "../../lib/api/clientes";

function slugify(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 40);
}

export default function ClientesPage() {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [nombre, setNombre] = useState("");
  const [sector, setSector] = useState("Holding");
  const [clienteIdManual, setClienteIdManual] = useState("");

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("socio_token") : null;
    if (!token) {
      router.replace("/");
      return;
    }

    let active = true;
    async function load(): Promise<void> {
      try {
        const list = await getClientes();
        if (!active) return;
        setClientes(list);
      } catch (err) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "No se pudo cargar la cartera de clientes.";
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [router]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return clientes;
    return clientes.filter((c) => {
      const s = `${c.nombre} ${c.cliente_id} ${c.sector ?? ""}`.toLowerCase();
      return s.includes(q);
    });
  }, [clientes, search]);

  async function handleCreateClient(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");

    const cleanName = nombre.trim();
    if (!cleanName) {
      setError("Ingresa un nombre de cliente.");
      return;
    }

    const rawId = clienteIdManual.trim() || slugify(cleanName);
    if (!rawId) {
      setError("No se pudo generar el identificador del cliente.");
      return;
    }

    setSaving(true);
    try {
      const created = await createCliente({
        cliente_id: rawId,
        nombre: cleanName,
        sector,
      });

      setClientes((prev) => [created, ...prev.filter((x) => x.cliente_id !== created.cliente_id)]);
      setNombre("");
      setSector("Holding");
      setClienteIdManual("");
      router.push(`/onboarding/${created.cliente_id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo crear el cliente.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteClient(cliente: ClienteOption): Promise<void> {
    const confirmed = window.confirm(
      `Vas a borrar el cliente "${cliente.nombre}" (${cliente.cliente_id}). Esta accion no se puede deshacer. Continuar?`,
    );
    if (!confirmed) return;

    setDeletingId(cliente.cliente_id);
    setError("");
    try {
      await deleteCliente(cliente.cliente_id);
      setClientes((prev) => prev.filter((item) => item.cliente_id !== cliente.cliente_id));
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo borrar el cliente.";
      setError(message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="min-h-screen bg-[#f7fafc]">
      <nav className="fixed top-0 w-full z-40 bg-white/85 backdrop-blur-xl border-b border-black/5 px-6 md:px-10 py-4 flex items-center justify-between">
        <div>
          <h1 className="font-headline text-3xl text-[#041627]">Socio AI</h1>
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Sovereign Intelligence</p>
        </div>
        <button
          type="button"
          onClick={() => {
            localStorage.removeItem("socio_token");
            router.push("/");
          }}
          className="sovereign-card !p-2 !px-3 text-[11px] uppercase tracking-[0.14em] text-slate-500 hover:text-[#041627]"
        >
          Cerrar sesion
        </button>
      </nav>

      <main className="pt-28 px-6 md:px-10 pb-12 max-w-[1440px] mx-auto">
        <header className="mb-10">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Cartera de clientes</p>
          <h2 className="font-headline text-5xl text-[#041627] mt-2">Selecciona un cliente o crea uno nuevo</h2>
          <p className="text-slate-600 mt-3 max-w-3xl">
            Flujo recomendado: 1) crear/seleccionar cliente, 2) responder onboarding, 3) cargar Trial Balance y Mayor, 4) arrancar auditoria.
          </p>
        </header>

        {error ? <div className="mb-6 sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">{error}</div> : null}

        <section className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          <article className="xl:col-span-7 sovereign-card">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
              <h3 className="font-headline text-3xl text-[#041627]">Clientes creados</h3>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nombre, sector o id"
                className="ghost-input w-full md:w-80"
              />
            </div>

            {loading ? (
              <div className="space-y-3">
                <div className="h-16 rounded-xl bg-[#f1f4f6] animate-pulse" />
                <div className="h-16 rounded-xl bg-[#f1f4f6] animate-pulse" />
                <div className="h-16 rounded-xl bg-[#f1f4f6] animate-pulse" />
              </div>
            ) : (
              <div className="space-y-3">
                {filtered.map((cliente) => (
                  <div key={cliente.cliente_id} className="rounded-xl border border-black/10 bg-[#f8fafc] p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div>
                      <p className="font-headline text-2xl text-[#041627]">{cliente.nombre}</p>
                      <p className="text-xs uppercase tracking-[0.14em] text-slate-500 mt-1">
                        ID: {cliente.cliente_id} · Sector: {cliente.sector || "Sin sector"}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => void handleDeleteClient(cliente)}
                        disabled={deletingId === cliente.cliente_id}
                        className="px-4 py-2 rounded-xl text-sm border border-[#ba1a1a]/30 text-[#93000a] bg-[#ffdad6]/40 hover:bg-[#ffdad6] disabled:opacity-60"
                      >
                        {deletingId === cliente.cliente_id ? "Borrando..." : "Borrar"}
                      </button>
                      <Link href={`/onboarding/${cliente.cliente_id}`} className="px-4 py-2 rounded-xl text-sm bg-white border border-black/10 text-slate-700 hover:bg-slate-50">
                        Onboarding
                      </Link>
                      <Link href={`/dashboard/${cliente.cliente_id}`} className="px-4 py-2 rounded-xl text-sm text-white" style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}>
                        Abrir dashboard
                      </Link>
                    </div>
                  </div>
                ))}
                {!filtered.length ? <p className="text-sm text-slate-500">No hay clientes con ese filtro.</p> : null}
              </div>
            )}
          </article>

          <article className="xl:col-span-5 sovereign-card">
            <h3 className="font-headline text-3xl text-[#041627]">Nuevo cliente</h3>
            <p className="text-sm text-slate-600 mt-2 mb-6">
              Al crear el cliente te llevo directo al onboarding para configurar preguntas clave y cargar archivos.
            </p>

            <form className="space-y-4" onSubmit={handleCreateClient}>
              <label className="flex flex-col gap-2">
                <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Nombre legal</span>
                <input className="ghost-input" value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Ej. Global Logistics Corp" />
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Cliente ID (opcional)</span>
                <input className="ghost-input" value={clienteIdManual} onChange={(e) => setClienteIdManual(e.target.value)} placeholder="si_99283_glc" />
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Sector</span>
                <select className="ghost-input" value={sector} onChange={(e) => setSector(e.target.value)}>
                  <option>Holding</option>
                  <option>Retail y Consumo</option>
                  <option>Logistica y Transporte</option>
                  <option>Tecnologia y SaaS</option>
                  <option>Manufactura</option>
                  <option>Servicios Financieros</option>
                  <option>Construccion e Infraestructura</option>
                  <option>Salud y Farmaceutico</option>
                  <option>Educacion</option>
                  <option>Energia y Utilities</option>
                  <option>Agroindustria</option>
                  <option>Gobierno y Sector Publico</option>
                  <option>ONG y Fundaciones</option>
                </select>
              </label>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 rounded-xl text-white font-semibold shadow-sm disabled:opacity-60"
                style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
              >
                {saving ? "Creando cliente..." : "Crear y continuar"}
              </button>
            </form>
          </article>
        </section>
      </main>
    </div>
  );
}
