import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Skeleton } from "./skeleton";

export interface Column<T> {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  /** Numbers are right-aligned and tabular so digits line up down the column. */
  align?: "left" | "right";
}

export interface DataTableProps<T> {
  columns: Array<Column<T>>;
  rows: T[];
  rowKey: (row: T) => string;
  /** Shown when `rows` is empty. Required -- an unexplained blank table reads as a bug. */
  empty: ReactNode;
  loading?: boolean;
  skeletonRows?: number;
  onRowClick?: (row: T) => void;
  "data-testid": string;
}

/**
 * DataTable. Presentation only, deliberately: sorting, filtering and paging stay
 * with the page so there is exactly one source of truth for what is on screen
 * and no hidden state to desynchronise from the URL.
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  empty,
  loading = false,
  skeletonRows = 5,
  onRowClick,
  ...rest
}: DataTableProps<T>) {
  if (!loading && rows.length === 0) {
    return <div {...rest}>{empty}</div>;
  }

  return (
    <div className="overflow-x-auto" {...rest}>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-line">
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                className={cn(
                  "px-3 py-2 text-xs font-medium tracking-wide text-muted uppercase",
                  c.align === "right" ? "text-right" : "text-left",
                )}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: skeletonRows }, (_, i) => (
                <tr key={i} className="border-b border-line last:border-0">
                  {columns.map((c) => (
                    <td key={c.key} className="px-3 py-2.5">
                      <Skeleton className="h-3.5 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            : rows.map((row) => (
                <tr
                  key={rowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(
                    "border-b border-line last:border-0",
                    onRowClick && "cursor-pointer hover:bg-canvas",
                  )}
                >
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={cn(
                        "px-3 py-2.5 text-body",
                        c.align === "right" ? "tabular text-right" : "text-left",
                      )}
                    >
                      {c.cell(row)}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}
