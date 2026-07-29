import type { AuditEvent } from "../hooks/useSSE";

export default function EventStream({ events }: { events: AuditEvent[] }) {
  return (
    <div className="max-h-80 overflow-auto rounded-lg border border-ink/10 bg-ink font-mono text-xs text-mist">
      {events.length === 0 && (
        <div className="p-3 text-mist/50">Waiting for audit events…</div>
      )}
      {events.map((e, i) => (
        <div key={e.event_id || i} className="border-b border-white/10 px-3 py-2">
          <span className="text-accent">{e.event_type}</span>{" "}
          {e.stage_id && <span className="text-warn">{e.stage_id}</span>}{" "}
          <span className="text-mist/70">{e.status}</span>
          {e.message && <div className="text-mist/50">{e.message}</div>}
        </div>
      ))}
    </div>
  );
}
