export default function AuditTable({
  events,
}: {
  events: Array<Record<string, unknown>>;
}) {
  return (
    <div className="overflow-auto rounded-lg border border-ink/10 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-mist/80 text-ink/60">
          <tr>
            <th className="px-3 py-2">Time</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">Stage</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e, i) => (
            <tr key={String(e.event_id || i)} className="border-t border-ink/5">
              <td className="px-3 py-2 font-mono text-xs">{String(e.timestamp || "")}</td>
              <td className="px-3 py-2">{String(e.event_type || "")}</td>
              <td className="px-3 py-2 font-mono text-xs">{String(e.stage_id || "")}</td>
              <td className="px-3 py-2">{String(e.status || "")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
