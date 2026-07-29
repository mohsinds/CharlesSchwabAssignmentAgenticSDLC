import { useState } from "react";
import { sendSignal } from "../api/client";

export function useApproval(runId: string | undefined) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function approve(stageId: string, notes = "") {
    if (!runId) return;
    setBusy(true);
    setError(null);
    try {
      await sendSignal(runId, { action: "approve", stage_id: stageId, notes });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function reject(stageId: string, reason: string) {
    if (!runId) return;
    setBusy(true);
    try {
      await sendSignal(runId, { action: "reject", stage_id: stageId, reason });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function safeStop(reason = "operator_stop") {
    if (!runId) return;
    setBusy(true);
    try {
      await sendSignal(runId, { action: "safe_stop", reason });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return { approve, reject, safeStop, busy, error };
}
