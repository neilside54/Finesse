/**
 * ScoreRing — a clean circular progress indicator for key chess metrics.
 * Swiss Design: thin precise lines, muted palette, no decorative fluff.
 * Uses CSS variables for dark mode compatibility.
 */

const STROKE_WIDTH = 3;
const SIZE = 100;

export interface ScoreRingProps {
  label: string;
  value: number;
  maxValue?: number;
  suffix?: string;
  color?: string;
  peerValue?: number;
  peerSource?: "actual" | "estimated";
  size?: number;
}

export function ScoreRing({
  label,
  value,
  maxValue = 100,
  suffix = "%",
  color,
  peerValue,
  peerSource,
  size = SIZE,
}: ScoreRingProps) {
  const clampedValue = Math.max(0, Math.min(maxValue, value));
  const progress = clampedValue / maxValue;
  const r = (size - STROKE_WIDTH) / 2;
  const circumference = 2 * Math.PI * r;
  const strokeDashoffset = circumference * (1 - progress);

  const peerProgress =
    peerValue !== undefined
      ? Math.max(0, Math.min(maxValue, peerValue)) / maxValue
      : null;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
        >
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            className="stroke-border"
            strokeWidth={STROKE_WIDTH}
          />
          {/* Peer ring (subtle outline behind) */}
          {peerProgress !== null && (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              className="stroke-muted-foreground/30"
              strokeWidth={STROKE_WIDTH + 4}
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - peerProgress)}
              strokeLinecap="butt"
            />
          )}
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color || "var(--accent)"}
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="butt"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        {/* Center value */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-2xl font-semibold tracking-tight text-foreground"
            style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
          >
            {Math.round(value)}
            <span className="text-sm font-normal text-muted-foreground">{suffix}</span>
          </span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-medium">
          {label}
        </p>
        {peerValue !== undefined && (
          <p className="text-[10px] text-muted-foreground/70 mt-0.5">
            Peers: {Math.round(peerValue)}{suffix}
            {peerSource === "estimated" && (
              <span className="ml-1 italic">(est.)</span>
            )}
          </p>
        )}
      </div>
    </div>
  );
}
