import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Status pill. The vocabulary is fixed in docs/design-system.md §6.
 *
 * Two rules are enforced by the type system rather than by documentation:
 *  1. `status` is a closed union, so a screen cannot invent a sixth state.
 *  2. `children` (the label) is required -- colour alone is never the signal,
 *     because colour-blind users and greyscale printouts exist. The glyph is
 *     reinforcement, and comes from the same table.
 */
export type Status =
  | "completed"
  | "on-pace"
  | "at-risk"
  | "overdue"
  | "scheduled"
  | "skipped";

const STYLES: Record<Status, { className: string; glyph: string; label: string }> = {
  completed: { className: "text-success bg-success-bg border-success-line", glyph: "check", label: "Completed" },
  "on-pace": { className: "text-success bg-success-bg border-success-line", glyph: "dash", label: "On pace" },
  "at-risk": { className: "text-warning bg-warning-bg border-warning-line", glyph: "bang", label: "At risk" },
  overdue: { className: "text-danger bg-danger-bg border-danger-line", glyph: "triangle", label: "Overdue" },
  scheduled: { className: "text-info bg-info-bg border-info-line", glyph: "circle", label: "Scheduled" },
  skipped: { className: "text-neutral-status bg-neutral-bg border-neutral-line", glyph: "dash", label: "Skipped" },
};

/**
 * Glyphs are inline SVG, never emoji or text characters. An emoji in a UI
 * string has no accessible name, scales inconsistently, and is banned
 * product-wide -- scripts/check_design_tokens.py fails the build on one.
 */
function Glyph({ kind }: { kind: string }) {
  const common = { "aria-hidden": true, viewBox: "0 0 12 12", className: "size-3 shrink-0" } as const;
  if (kind === "check") {
    return (
      <svg {...common}>
        <path d="M2 6.4 4.6 9 10 3.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (kind === "bang") {
    return (
      <svg {...common}>
        <path d="M6 1.5v5.2M6 9.4v1.1" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }
  if (kind === "triangle") {
    return (
      <svg {...common}>
        <path d="M6 1.6 11.2 10.4H0.8L6 1.6Z" fill="currentColor" />
      </svg>
    );
  }
  if (kind === "circle") {
    return (
      <svg {...common}>
        <circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.6" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <path d="M2.5 6h7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export interface StatusPillProps {
  status: Status;
  /** Overrides the default label, e.g. "Overdue · 3d". The label is never omitted. */
  label?: ReactNode;
  "data-testid": string;
}

export function StatusPill({ status, label, ...rest }: StatusPillProps) {
  const s = STYLES[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        s.className,
      )}
      {...rest}
    >
      <Glyph kind={s.glyph} />
      {label ?? s.label}
    </span>
  );
}
