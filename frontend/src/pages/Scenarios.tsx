import { Link } from "react-router-dom";

const ITEMS = [
  {
    id: "greenfield",
    title: "Greenfield URL shortener",
    body: "From a clear prompt, run the full DAG and produce APIs, tests, and docs.",
  },
  {
    id: "brownfield",
    title: "Brownfield rate limit + cache",
    body: "Ingest seed repo, retrieve context, and propose targeted changes.",
  },
  {
    id: "ambiguous",
    title: "Ambiguous enterprise-ready",
    body: "Classifier routes to clarifier HITL, then replans from requirement.",
  },
];

export default function Scenarios() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold">Scenarios</h1>
      <div className="grid gap-4 md:grid-cols-3">
        {ITEMS.map((s) => (
          <div key={s.id} className="rounded-lg border border-ink/10 bg-white p-4">
            <h2 className="font-semibold">{s.title}</h2>
            <p className="mt-2 text-sm text-ink/70">{s.body}</p>
            <Link to="/" className="mt-3 inline-block text-sm font-medium text-accent">
              Run from home →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
