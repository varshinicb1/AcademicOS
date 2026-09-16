import Link from "next/link";
import type { ReactNode } from "react";

/**
 * Page header. Every screen uses this, so the title's size, the breadcrumb's
 * position and the action cluster's alignment are decided once.
 *
 * Breadcrumbs are omitted rather than faked when a screen is top-level; a
 * single-item breadcrumb is noise.
 */
export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  ...rest
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  "data-testid"?: string;
}) {
  return (
    <div className="mb-6" {...rest}>
      {breadcrumbs && breadcrumbs.length > 0 ? (
        <nav aria-label="Breadcrumb" className="mb-2">
          <ol className="flex items-center gap-1.5 text-xs text-muted">
            {breadcrumbs.map((crumb, i) => (
              <li key={`${crumb.label}-${i}`} className="flex items-center gap-1.5">
                {i > 0 ? (
                  <span aria-hidden="true" className="text-line-strong">
                    /
                  </span>
                ) : null}
                {crumb.href ? (
                  <Link href={crumb.href} className="hover:text-body">
                    {crumb.label}
                  </Link>
                ) : (
                  <span aria-current="page">{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      ) : null}

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-ink">{title}</h1>
          {description ? (
            <p className="mt-1 max-w-2xl text-sm text-body">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
    </div>
  );
}
