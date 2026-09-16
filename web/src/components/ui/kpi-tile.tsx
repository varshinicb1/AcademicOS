import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type DeltaDirection = "up" | "down" | "flat";
export type DeltaTone = "good" | "bad" | "neutral";

/**
 * A single headline number.
 *
 * Two things are deliberate:
 *  1. The value is always `tabular`. Proportional digits make a row of KPI
 *     tiles jitter as values change, which defeats side-by-side comparison.
 *  2. A delta is never communicated by colour alone. It carries an arrow and a
 *     screen-reader phrase, so "down 4%" is legible without colour vision.
 */
export function KpiTile({
  label,
  value,
  unit,
  delta,
  deltaLabel,
  hint,
  className,
  ...rest
}: {
  label: ReactNode;
  value: ReactNode;
  unit?: ReactNode;
  delta?: { direction: DeltaDirection; value: ReactNode; tone?: DeltaTone };
  /** Spoken form of the delta, e.g. "down 4 percent against last week". */
  deltaLabel?: string;
  hint?: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  const tone = delta?.tone ?? "neutral";
  const toneClass = {
    good: "text-success",
    bad: "text-danger",
    neutral: "text-muted",
  }[tone];

  return (
    <div
      className={cn("rounded-lg border border-line bg-card px-4 py-3 shadow-sm", className)}
      {...rest}
    >
      <div className="text-xs font-medium tracking-wide text-muted uppercase">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-1">
        <span className="tabular text-3xl font-semibold text-ink">{value}</span>
        {unit ? <span className="text-sm text-muted">{unit}</span> : null}
      </div>
      {delta ? (
        <div className={cn("mt-1 flex items-center gap-1 text-sm", toneClass)}>
          <DeltaArrow direction={delta.direction} />
          <span className="tabular">{delta.value}</span>
          {deltaLabel ? <span className="sr-only">{deltaLabel}</span> : null}
        </div>
      ) : null}
      {hint ? <div className="mt-1 text-xs text-muted">{hint}</div> : null}
    </div>
  );
}

function DeltaArrow({ direction }: { direction: DeltaDirection }) {
  const common = { "aria-hidden": true, viewBox: "0 0 12 12", className: "size-3 shrink-0" } as const;
  if (direction === "flat") {
    return (
      <svg {...common}>
        <path d="M2.5 6h7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <g transform={direction === "down" ? "rotate(180 6 6)" : undefined}>
        <path
          d="M6 9.5V2.5M2.8 5.7 6 2.5l3.2 3.2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    </svg>
  );
}
