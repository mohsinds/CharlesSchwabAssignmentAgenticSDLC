export type DagStage = {
  id: string;
  requires_hitl?: boolean;
  terminal?: boolean;
};

export function layoutStages(stages: DagStage[]): DagStage[] {
  return stages;
}

export function statusColor(status?: string): string {
  switch (status) {
    case "completed":
      return "bg-ok text-white";
    case "running":
      return "bg-accent text-white";
    case "waiting_hitl":
      return "bg-warn text-white";
    case "failed":
    case "rejected":
    case "gate_failed":
      return "bg-red-700 text-white";
    default:
      return "bg-ink/10 text-ink/60";
  }
}
