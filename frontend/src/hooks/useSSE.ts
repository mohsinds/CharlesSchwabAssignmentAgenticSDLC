import { useEffect, useState } from "react";
import { eventsUrl } from "../api/client";

export type AuditEvent = {
  event_id?: string;
  event_type: string;
  stage_id?: string;
  status?: string;
  message?: string;
  timestamp?: string;
  payload?: Record<string, unknown>;
};

export function useSSE(runId: string | undefined) {
  const [events, setEvents] = useState<AuditEvent[]>([]);

  useEffect(() => {
    if (!runId) return;
    const es = new EventSource(eventsUrl(runId));
    es.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.event_type === "stream_end") {
          es.close();
          return;
        }
        setEvents((prev) => [...prev, data]);
      } catch {
        /* ignore */
      }
    };
    es.onerror = () => {
      es.close();
    };
    return () => es.close();
  }, [runId]);

  return { events };
}
