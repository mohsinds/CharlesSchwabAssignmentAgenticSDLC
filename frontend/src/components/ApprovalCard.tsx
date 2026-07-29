import { useState } from "react";

export default function ApprovalCard({
  stageId,
  onApprove,
  onReject,
  busy,
}: {
  stageId: string;
  onApprove: (notes: string) => void;
  onReject: (reason: string) => void;
  busy?: boolean;
}) {
  const [notes, setNotes] = useState("");

  return (
    <div className="rounded-lg border border-warn/30 bg-white p-4 shadow-sm">
      <h3 className="font-display text-base font-semibold text-ink">
        Human approval required
      </h3>
      <p className="mt-1 text-sm text-ink/70">
        Stage <span className="font-mono text-accent">{stageId}</span> is waiting.
      </p>
      <textarea
        className="mt-3 w-full rounded border border-ink/15 bg-mist/50 p-2 text-sm"
        rows={3}
        placeholder="Clarification notes or approval comment"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
      <div className="mt-3 flex gap-2">
        <button
          disabled={busy}
          onClick={() => onApprove(notes)}
          className="rounded bg-ok px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Approve
        </button>
        <button
          disabled={busy}
          onClick={() => onReject(notes || "rejected")}
          className="rounded bg-ink/80 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
