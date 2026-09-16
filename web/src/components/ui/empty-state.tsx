import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Empty state. Every list, table and chart in this product can be empty, and an
 * empty screen is where users most often conclude the product is broken. So the
 * shape is mandatory: what this is, why it is empty, and the one action that
 * changes that. `title` and `description` are required for that reason.
 *
 * `action` is optional only because some empty states genuinely have no
 * action (e.g. "no alerts" is good news).
 */
export function EmptyState({
  title,
  description,
  action,
  secondaryAction,
  className,
  ...rest
}: {
  title: ReactNode;
  description: ReactNode;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center px-6 py-12 text-center", className)}
      {...rest}
    >
      <div className="mb-4 flex size-10 items-center justify-center rounded-full border border-line bg-inset">
        <svg aria-hidden="true" viewBox="0 0 20 20" className="size-5 text-muted">
          <path
            d="M3 5.5h14M3 10h14M3 14.5h9"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-body">{description}</p>
      {action || secondaryAction ? (
        <div className="mt-5 flex items-center gap-2">
          {action}
          {secondaryAction}
        </div>
      ) : null}
    </div>
  );
}
