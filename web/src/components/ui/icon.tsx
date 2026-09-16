import type { ReactNode } from "react";

/**
 * A closed icon set, drawn inline.
 *
 * No icon package: the product needs about a dozen glyphs, and a dependency
 * here would be a second visual vocabulary the design-token checker cannot see.
 * Strokes are 1.6 at a 20px box, matching the weight of the 14px body text they
 * sit beside.
 *
 * Emoji are not an option anywhere in this product (design-system.md §11), and
 * scripts/check_design_tokens.py fails the build if one appears.
 */
export type IconName =
  | "dashboard"
  | "curriculum"
  | "question"
  | "papers"
  | "assessments"
  | "practice"
  | "scan"
  | "evaluations"
  | "insights"
  | "schools"
  | "users"
  | "consent"
  | "gallery"
  | "search"
  | "bell";

const PATHS: Record<IconName, ReactNode> = {
  dashboard: (
    <path d="M3 3h6v6H3zM11 3h6v4h-6zM11 9h6v8h-6zM3 11h6v6H3z" />
  ),
  curriculum: (
    <path d="M4 3h7a2 2 0 0 1 2 2v12a2 2 0 0 0-2-2H4zM16 3h-2a2 2 0 0 0-2 2v12a2 2 0 0 1 2-2h2z" />
  ),
  question: (
    <>
      <circle cx="10" cy="10" r="7" />
      <path d="M8 8a2 2 0 1 1 2.7 1.9c-.5.2-.7.6-.7 1.1v.5M10 14v.5" />
    </>
  ),
  papers: <path d="M5 3h7l4 4v10H5zM12 3v4h4" />,
  assessments: (
    <>
      <rect x="4" y="3" width="12" height="14" rx="1.5" />
      <path d="M7 8h6M7 11h6M7 14h3" />
    </>
  ),
  practice: <path d="M4 10a6 6 0 1 1 2 4.5M4 16v-3h3" />,
  scan: (
    <>
      <rect x="3" y="3" width="14" height="14" rx="1.5" />
      <path d="M3 7h14M7 3v14" />
    </>
  ),
  evaluations: <path d="M6 3h8v3H6zM5 4.5H4V17h12V4.5h-1M7 11l2 2 4-4" />,
  insights: <path d="M5 16h2.5V9H5zM9.75 16h2.5V4h-2.5zM14.5 16h2.5v-6h-2.5z" />,
  schools: (
    <path d="M10 2 3 5v2h14V5zM4.5 8h2v6h-2zM9 8h2v6H9zM13.5 8h2v6h-2zM3 15h14v3H3z" />
  ),
  users: (
    <>
      <circle cx="8" cy="7" r="3" />
      <path d="M3 17c0-2.5 2.2-4 5-4s5 1.5 5 4M14 6.5a3 3 0 0 1 0 5.8M15 17c0-1.6-.5-2.9-1.4-3.7" />
    </>
  ),
  consent: <path d="M10 2.5 4 5v5c0 4 2.6 6.5 6 7.5 3.4-1 6-3.5 6-7.5V5z" />,
  gallery: (
    <>
      <rect x="3" y="3" width="6" height="6" rx="1" />
      <rect x="11" y="3" width="6" height="6" rx="1" />
      <rect x="3" y="11" width="6" height="6" rx="1" />
      <rect x="11" y="11" width="6" height="6" rx="1" />
    </>
  ),
  search: (
    <>
      <circle cx="9" cy="9" r="5.5" />
      <path d="m13 13 4 4" />
    </>
  ),
  bell: <path d="M10 3a4.5 4.5 0 0 0-4.5 4.5c0 3.5-1.5 5-1.5 5h12s-1.5-1.5-1.5-5A4.5 4.5 0 0 0 10 3zM8.5 15.5a1.7 1.7 0 0 0 3 0" />,
};

const FILLED: ReadonlySet<IconName> = new Set(["dashboard", "schools", "insights"]);

export function Icon({ name, className }: { name: IconName; className?: string }) {
  const filled = FILLED.has(name);
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      className={className ?? "size-5 shrink-0"}
      fill={filled ? "currentColor" : "none"}
      stroke={filled ? "none" : "currentColor"}
      strokeWidth={filled ? undefined : 1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {PATHS[name]}
    </svg>
  );
}
