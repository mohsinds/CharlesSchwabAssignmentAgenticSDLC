import { useCallback, useEffect, useState } from "react";
import { getPipeline, type Pipeline } from "../api/client";

export function usePipeline(runId: string | undefined, intervalMs = 1500) {
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!runId) return;
    try {
      const p = await getPipeline(runId);
      setPipeline(p);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [runId]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return { pipeline, error, refresh };
}
