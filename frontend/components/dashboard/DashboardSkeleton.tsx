export default function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <section className="sovereign-card animate-pulse space-y-3">
        <div className="h-3 w-44 rounded" style={{ backgroundColor: "#EDF2F7" }} />
        <div className="h-10 w-80 rounded" style={{ backgroundColor: "#EDF2F7" }} />
        <div className="h-4 w-72 rounded" style={{ backgroundColor: "#EDF2F7" }} />
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {Array.from({ length: 5 }).map((_, index) => (
          <article key={index} className="sovereign-card animate-pulse space-y-3">
            <div className="h-3 w-24 rounded" style={{ backgroundColor: "#EDF2F7" }} />
            <div className="h-8 w-32 rounded" style={{ backgroundColor: "#EDF2F7" }} />
            <div className="h-3 w-28 rounded" style={{ backgroundColor: "#EDF2F7" }} />
          </article>
        ))}
      </section>

      <section className="ai-memo animate-pulse space-y-3">
        <div className="h-3 w-44 rounded bg-teal-100/40" />
        <div className="h-4 w-full rounded bg-teal-100/30" />
        <div className="h-4 w-5/6 rounded bg-teal-100/30" />
        <div className="h-4 w-4/6 rounded bg-teal-100/30" />
      </section>
    </div>
  );
}
