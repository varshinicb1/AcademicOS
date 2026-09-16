import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Card. The only elevation-1 container in the product (design-system.md §5).
 * Cards sit on the off-white canvas; a card is never nested inside a card,
 * because two shadows at once has no meaning in this hierarchy.
 */
export function Card({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border border-line bg-card shadow-sm", className)}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  description,
  actions,
  ...rest
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  "data-testid"?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-line px-4 py-3" {...rest}>
      <div className="min-w-0">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        {description ? <p className="mt-0.5 text-sm text-body">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function CardBody({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-4 py-3", className)} {...rest}>
      {children}
    </div>
  );
}
