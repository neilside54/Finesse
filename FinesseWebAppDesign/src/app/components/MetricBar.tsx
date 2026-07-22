/**
 * MetricBar — Swiss Design progress bar for detailed metric sections.
 * Warm walnut palette: gold filled, green better, red worse, warm empty.
 */

export interface MetricVisual {
  bars?: number;
  status?: "better" | "worse" | "equal" | "unknown";
  color?: "green" | "red" | "yellow" | "grey";
}

export interface MetricBarProps {
  label: string;
  value: number;
  peerValue?: number;
  peerSource?: "actual" | "estimated";
  visual?: MetricVisual;
  suffix?: string;
  sampleNote?: string;
}

const STATUS_CLASSES: Record<string, { text: string; fill: string }> = {
  better: { text: "text-[#7A9E5F]", fill: "#7A9E5F" },
  worse: { text: "text-[#B85C4A]", fill: "#B85C4A" },
  equal: { text: "text-[#A89070]", fill: "#C8A96E" },
  unknown: { text: "text-[#A89070]", fill: "#C8A96E" },
};

export function MetricBar({
  label,
  value,
  peerValue,
  peerSource,
  visual,
  suffix = "%",
  sampleNote,
}: MetricBarProps) {
  const fillPercent = Math.max(0, Math.min(100, value));
  const peerPercent =
    peerValue !== undefined ? Math.max(0, Math.min(100, peerValue)) : null;

  const status = visual?.status ?? "unknown";
  const styles = STATUS_CLASSES[status] ?? STATUS_CLASSES.unknown;

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-[#F0E6D3]">{label}</span>
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold tabular-nums text-[#F0E6D3]">
            {typeof value === "number" ? value.toFixed(1) : value}
            {suffix}
          </span>
          {peerValue != null && (
            <span className="text-xs text-[#A89070] tabular-nums">
              vs {peerValue!.toFixed(1)}
              {suffix}
              {peerSource === "estimated" && (
                <span className="ml-0.5 italic">(est.)</span>
              )}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative h-1.5 w-full bg-[#2E2016]">
        {/* Peer marker */}
        {peerPercent !== null && (
          <div
            className="absolute top-0 h-full w-px bg-[#A89070]/50"
            style={{ left: `${peerPercent}%` }}
          />
        )}
        {/* Fill */}
        <div
          className="absolute top-0 h-full transition-all duration-700 ease-out"
          style={{
            width: `${fillPercent}%`,
            backgroundColor: styles.fill,
          }}
        />
      </div>

      {/* Status label */}
      <div className="flex items-center justify-between">
        {visual?.status && visual.status !== "unknown" && (
          <span
            className={`text-[10px] font-medium uppercase tracking-[0.15em] ${styles.text}`}
          >
            {status === "better"
              ? "better than peers"
              : status === "worse"
              ? "worse than peers"
              : "in line with peers"}
          </span>
        )}
        {peerSource === "estimated" && (
          <span className="text-[10px] font-medium uppercase tracking-[0.15em] text-[#A89070] border border-[#3D2B1A] px-1.5 py-0.5">
            estimated
          </span>
        )}
        {sampleNote && (
          <span className="text-[10px] text-[#A89070] italic">
            {sampleNote}
          </span>
        )}
      </div>
    </div>
  );
}
