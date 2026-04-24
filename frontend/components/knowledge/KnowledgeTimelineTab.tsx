"use client";

import type { KnowledgeEvent } from "../../types/knowledge";

type Props = {
  events: KnowledgeEvent[];
  isLoading?: boolean;
};

export default function KnowledgeTimelineTab({ events, isLoading = false }: Props) {
  return (
    <section className="sovereign-card p-5 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-headline text-2xl text-[#041627]">Timeline</h2>
        <p className="text-xs text-slate-500">Eventos: {events.length}</p>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Cargando timeline...</p>
      ) : events.length === 0 ? (
        <p className="text-sm text-slate-500">Sin eventos recientes.</p>
      ) : (
        <ul className="space-y-2">
          {events.map((event) => (
            <li key={event.id} className="border border-[#041627]/10 rounded-editorial p-3">
              <p className="text-sm font-semibold text-[#041627]">{event.event_type}</p>
              <p className="text-xs text-slate-500">
                modulo: {event.source_module || "-"} · source: {event.source_id || "-"}
              </p>
              <p className="text-xs text-slate-500">{event.created_at || "-"}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

