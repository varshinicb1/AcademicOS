import { cn } from "@/lib/cn";

/**
 * Skeleton. Used while data is in flight so layout does not jump when it
 * arrives. A skeleton that does not match the shape of the thing it replaces is
 * worse than none at all, so callers pass the real dimensions.
 */
export function Skeleton({
  className,
  ...rest
}: { className?: string; "data-testid"?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded-sm bg-inset", className)}
      {...rest}
    />
  );
}

/** A stack of skeleton lines for text blocks. The last line is short, as real text is. */
export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} className={cn("h-3", i === lines - 1 ? "w-2/5" : "w-full")} />
      ))}
    </div>
  );
}
