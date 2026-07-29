import { Link, useParams } from "react-router-dom";
import ApprovalCard from "../components/ApprovalCard";
import DagView from "../components/DagView";
import EventStream from "../components/EventStream";
import { useApproval } from "../hooks/useApproval";
import { usePipeline } from "../hooks/usePipeline";
import { useSSE } from "../hooks/useSSE";

export default function Pipeline() {
  const { runId } = useParams();
  const { pipeline, error } = usePipeline(runId);
  const { events } = useSSE(runId);
  const { approve, reject, safeStop, busy } = useApproval(runId);

  const waitingStage =
    pipeline?.status === "waiting_hitl"
      ? pipeline.current_stage ||
        Object.entries(pipeline.stage_status).find(([, v]) => v === "waiting_hitl")?.[0]
      : null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold">Pipeline</h1>
          <p className="font-mono text-xs text-ink/50">{runId}</p>
          <p className="mt-1 text-sm">
            Status: <span className="font-semibold">{pipeline?.status || "…"}</span>
            {pipeline?.mode && (
              <span className="ml-2 rounded bg-ink/5 px-2 py-0.5 font-mono text-xs">
                {pipeline.mode}
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/audit/${runId}`}
            className="rounded border border-ink/15 bg-white px-3 py-1.5 text-sm"
          >
            Audit
          </Link>
          <button
            type="button"
            onClick={() => safeStop()}
            className="rounded border border-warn/40 bg-white px-3 py-1.5 text-sm text-warn"
          >
            Safe stop
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink/50">DAG</h2>
        <DagView
          stageStatus={pipeline?.stage_status || {}}
          currentStage={pipeline?.current_stage}
        />
      </section>

      {waitingStage && (
        <ApprovalCard
          stageId={waitingStage}
          busy={busy}
          onApprove={(notes) => approve(waitingStage, notes)}
          onReject={(reason) => reject(waitingStage, reason)}
        />
      )}

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink/50">
          Live events
        </h2>
        <EventStream events={events} />
      </section>
    </div>
  );
}
