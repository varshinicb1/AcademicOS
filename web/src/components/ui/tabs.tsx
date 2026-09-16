"use client";

import { useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface Tab {
  id: string;
  label: ReactNode;
}

/**
 * Tabs. Implements the WAI-ARIA tabs pattern rather than looking like it:
 * roving arrow-key focus, a single tab stop, and `aria-controls` wired to real
 * panels. Getting this wrong is invisible to sighted mouse users and breaks
 * keyboard users completely, so it is done properly here once.
 */
export function Tabs({
  tabs,
  value,
  onChange,
  panels,
  className,
  ...rest
}: {
  tabs: Tab[];
  value: string;
  onChange: (id: string) => void;
  panels: Record<string, ReactNode>;
  className?: string;
  "data-testid": string;
}) {
  const base = useId();
  const refs = useRef(new Map<string, HTMLButtonElement>());

  const move = (delta: number) => {
    const i = tabs.findIndex((t) => t.id === value);
    if (i === -1) return;
    const next = tabs[(i + delta + tabs.length) % tabs.length];
    if (!next) return;
    onChange(next.id);
    refs.current.get(next.id)?.focus();
  };

  return (
    <div className={className} {...rest}>
      <div role="tablist" className="flex items-center gap-1 border-b border-line">
        {tabs.map((t) => {
          const selected = t.id === value;
          return (
            <button
              key={t.id}
              ref={(el) => {
                if (el) refs.current.set(t.id, el);
                else refs.current.delete(t.id);
              }}
              type="button"
              role="tab"
              id={`${base}-tab-${t.id}`}
              aria-controls={`${base}-panel-${t.id}`}
              aria-selected={selected}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(t.id)}
              onKeyDown={(e) => {
                if (e.key === "ArrowRight") { e.preventDefault(); move(1); }
                else if (e.key === "ArrowLeft") { e.preventDefault(); move(-1); }
                else if (e.key === "Home") { e.preventDefault(); onChange(tabs[0]?.id ?? value); }
                else if (e.key === "End") { e.preventDefault(); onChange(tabs[tabs.length - 1]?.id ?? value); }
              }}
              className={cn(
                "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors duration-[var(--duration-fast)]",
                selected
                  ? "border-brand text-ink"
                  : "border-transparent text-muted hover:border-line-strong hover:text-body",
              )}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      {tabs.map((t) => (
        <div
          key={t.id}
          role="tabpanel"
          id={`${base}-panel-${t.id}`}
          aria-labelledby={`${base}-tab-${t.id}`}
          hidden={t.id !== value}
          tabIndex={0}
          className="pt-4"
        >
          {t.id === value ? panels[t.id] : null}
        </div>
      ))}
    </div>
  );
}
