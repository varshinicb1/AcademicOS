import Link from "next/link";
import { Icon } from "@/components/ui/icon";

/**
 * Top bar.
 *
 * The search affordance is a link, not an input. A text field that swallows
 * keystrokes and does nothing is worse than no field at all -- it teaches the
 * user the product is slow rather than unfinished. When `/search` lands in
 * Phase 3 this becomes the input, pointing at the same route.
 */
export function Topbar({ onMenuClick }: { onMenuClick?: () => void }) {
  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-3 border-b border-line bg-card px-4">
      {onMenuClick ? (
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation"
          className="-ml-1 flex size-8 items-center justify-center rounded-md text-body hover:bg-inset md:hidden"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" className="size-5">
            <path
              d="M3 5.5h14M3 10h14M3 14.5h14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        </button>
      ) : null}

      <Link
        href="/search"
        data-testid="global-search"
        className="flex h-8 max-w-md flex-1 items-center gap-2 rounded-md border border-line bg-canvas px-3 text-sm text-muted hover:border-line-strong hover:text-body"
      >
        <Icon name="search" className="size-4 shrink-0" />
        <span>Search students, papers, topics</span>
      </Link>

      <div className="ml-auto flex items-center gap-1">
        <Link
          href="/notifications"
          aria-label="Notifications"
          className="flex size-8 items-center justify-center rounded-md text-body hover:bg-inset"
        >
          <Icon name="bell" className="size-5" />
        </Link>
        <div
          aria-hidden="true"
          className="ml-1 flex size-7 items-center justify-center rounded-full bg-brand-subtle text-xs font-medium text-brand"
        >
          AO
        </div>
      </div>
    </header>
  );
}
