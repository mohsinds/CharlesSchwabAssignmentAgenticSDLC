import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPipeline } from "../api/client";

const SCENARIOS = [
  {
    id: "greenfield",
    label: "Greenfield",
    prompt:
      "Build a URL shortener with POST /shorten, GET /{code} redirect, click analytics, and health checks.",
  },
  {
    id: "brownfield",
    label: "Brownfield",
    prompt: "Add rate limiting and a Redis cache to the existing URL shortener service.",
  },
  {
    id: "ambiguous",
    label: "Ambiguous",
    prompt: "Make the URL shortener enterprise-ready.",
  },
] as const;

export default function Home() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState<string>(SCENARIOS[0].prompt);
  const [scenario, setScenario] = useState<string | null>("greenfield");
  const [mode, setMode] = useState<"live" | "replay">("replay");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onStart() {
    setBusy(true);
    setError(null);
    try {
      const p = await createPipeline({
        prompt,
        scenario_type: scenario,
        mode,
      });
      navigate(`/pipelines/${p.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-bold tracking-tight text-ink">Agentic SDLC</h1>
      <p className="mt-2 text-lg text-ink/70">
        Send a requirement. The Temporal DAG orchestrates classify → design → implement → test →
        release with policy gates and human checkpoints.
      </p>

      <div className="mt-6 flex flex-wrap gap-2">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => {
              setScenario(s.id);
              setPrompt(s.prompt);
            }}
            className={`rounded px-3 py-1.5 text-sm font-medium ${
              scenario === s.id ? "bg-accent text-white" : "bg-white text-ink/70 border border-ink/10"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <textarea
        className="mt-4 w-full rounded-lg border border-ink/15 bg-white/80 p-4 text-base shadow-sm"
        rows={6}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />

      <div className="mt-4 flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            checked={mode === "replay"}
            onChange={() => setMode("replay")}
          />
          Replay (offline demo)
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="radio" checked={mode === "live"} onChange={() => setMode("live")} />
          Live (LiteLLM)
        </label>
        <button
          type="button"
          disabled={busy || !prompt.trim()}
          onClick={onStart}
          className="ml-auto rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {busy ? "Starting…" : "Start pipeline"}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
    </div>
  );
}
