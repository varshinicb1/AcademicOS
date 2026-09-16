"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/ui/icon";
import { NAV } from "@/lib/nav";
import { cn } from "@/lib/cn";

/**
 * Active-route detection. `/` is an exact match only -- otherwise every route
 * would light up Dashboard. Section routes match by prefix so `/papers/123`
 * keeps Papers highlighted.
 */
function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-60 shrink-0 flex-col border-r border-line bg-card">
      <div className="flex h-14 shrink-0 items-center gap-2 border-b border-line px-4">
        <div className="flex size-6 items-center justify-center rounded-sm bg-brand text-white">
          <svg aria-hidden="true" viewBox="0 0 20 20" className="size-4">
            <path
              d="M10 3.2 3.6 6.4 10 9.6l6.4-3.2z"
              fill="currentColor"
            />
            <path
              d="M5.8 9v4.2c0 .9 1.9 1.9 4.2 1.9s4.2-1 4.2-1.9V9"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <span className="text-sm font-semibold text-ink">AcademicOS</span>
      </div>

      <nav aria-label="Main" className="flex-1 overflow-y-auto px-2 py-3">
        {NAV.map((section) => (
          <div key={section.label} className="mb-4 last:mb-0">
            <div className="px-2 pb-1 text-2xs font-medium tracking-wide text-muted uppercase">
              {section.label}
            </div>
            <ul>
              {section.items.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      aria-current={active ? "page" : undefined}
                      data-testid={`nav-${item.href === "/" ? "dashboard" : item.href.slice(1)}`}
                      title={`Backend module: ${item.module}`}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors duration-[var(--duration-fast)]",
                        active
                          ? "bg-brand-subtle font-medium text-brand"
                          : "text-body hover:bg-inset hover:text-ink",
                      )}
                    >
                      <Icon name={item.icon} className="size-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </div>
  );
}
