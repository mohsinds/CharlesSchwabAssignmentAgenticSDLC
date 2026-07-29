import { statusColor } from "../lib/dagLayout";

const DEFAULT_STAGES = [
  "classify",
  "clarify",
  "codebase_ingest",
  "requirement",
  "design",
  "implementation_plan",
  "test_plan",
  "implementation",
  "test",
  "documentation",
  "release_review",
];

export default function DagView({
  stageStatus,
  currentStage,
}: {
  stageStatus: Record<string, string>;
  currentStage?: string | null;
}) {
  const stages = Array.from(
    new Set([...DEFAULT_STAGES, ...Object.keys(stageStatus)])
  );

  return (
    <div className="flex flex-wrap gap-2">
      {stages.map((id) => {
        const st = stageStatus[id] || (id === currentStage ? "running" : "pending");
        return (
          <div
            key={id}
            className={`rounded px-3 py-2 font-mono text-xs ${statusColor(st)}`}
            title={st}
          >
            <div className="font-semibold">{id}</div>
            <div className="opacity-80">{st}</div>
          </div>
        );
      })}
    </div>
  );
}
