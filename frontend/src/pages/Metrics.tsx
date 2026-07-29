import { useEffect, useState } from "react";
import { getMetrics } from "../api/client";
import MetricTiles from "../components/MetricTiles";

export default function Metrics() {
  const [metrics, setMetrics] = useState<{
    pipelines_total?: number;
    by_status?: Record<string, number>;
  }>({});

  useEffect(() => {
    getMetrics().then(setMetrics);
    const id = setInterval(() => getMetrics().then(setMetrics), 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold">Reliability metrics</h1>
      <p className="text-sm text-ink/60">
        In-process counters. Prometheus scrape: <code>/metrics/prometheus</code>. Grafana dashboard
        ships in compose.
      </p>
      <MetricTiles metrics={metrics} />
    </div>
  );
}
