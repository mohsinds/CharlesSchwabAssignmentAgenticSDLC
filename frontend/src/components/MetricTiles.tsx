export default function MetricTiles({
  metrics,
}: {
  metrics: { pipelines_total?: number; by_status?: Record<string, number> };
}) {
  const entries = Object.entries(metrics.by_status || {});
  return (
    <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
      <div className="rounded-lg border border-ink/10 bg-white p-4">
        <div className="text-xs uppercase tracking-wide text-ink/50">Pipelines</div>
        <div className="mt-1 font-display text-3xl font-semibold">
          {metrics.pipelines_total ?? 0}
        </div>
      </div>
      {entries.map(([k, v]) => (
        <div key={k} className="rounded-lg border border-ink/10 bg-white p-4">
          <div className="text-xs uppercase tracking-wide text-ink/50">{k}</div>
          <div className="mt-1 font-display text-3xl font-semibold">{v}</div>
        </div>
      ))}
    </div>
  );
}
