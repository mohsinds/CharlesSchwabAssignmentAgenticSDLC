const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export type Pipeline = {
  run_id: string;
  workflow_id: string;
  status: string;
  current_stage?: string | null;
  stage_status: Record<string, string>;
  scenario_type?: string | null;
  mode: string;
  artifacts?: Record<string, unknown>;
};

export async function createPipeline(body: {
  prompt: string;
  scenario_type?: string | null;
  mode: "live" | "replay";
}): Promise<Pipeline> {
  const res = await fetch(`${API_BASE}/pipelines`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPipeline(runId: string): Promise<Pipeline> {
  const res = await fetch(`${API_BASE}/pipelines/${runId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDag() {
  const res = await fetch(`${API_BASE}/pipelines/meta/dag`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function sendSignal(
  runId: string,
  body: {
    action: "approve" | "reject" | "replan" | "safe_stop";
    stage_id?: string;
    notes?: string;
    reason?: string;
    from_stage?: string;
    hint?: string;
  }
) {
  const res = await fetch(`${API_BASE}/signals/${runId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAudit(runId: string) {
  const res = await fetch(`${API_BASE}/audit/${runId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function eventsUrl(runId: string) {
  return `${API_BASE}/pipelines/${runId}/events`;
}
