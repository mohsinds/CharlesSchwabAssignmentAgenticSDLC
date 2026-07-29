import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getAudit } from "../api/client";
import AuditTable from "../components/AuditTable";

export default function Audit() {
  const { runId } = useParams();
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [summary, setSummary] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (!runId) return;
    getAudit(runId).then((data) => {
      setEvents(data.events || []);
      setSummary(data.summary || {});
    });
  }, [runId]);

  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold">Audit trail</h1>
      <p className="font-mono text-xs text-ink/50">{runId}</p>
      <pre className="rounded bg-white p-3 text-xs">{JSON.stringify(summary, null, 2)}</pre>
      <AuditTable events={events} />
    </div>
  );
}
