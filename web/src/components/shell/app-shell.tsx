"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

/**
 * App shell.
 *
 * A client component only because the mobile drawer needs state. `children`
 * still arrives as a server-rendered payload, so no screen has to become
 * client-side just because it lives inside the shell.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();

  // A drawer that stays open across a navigation covers the page the user just
  // asked for.
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  return (
    <div className="flex min-h-screen bg-canvas">
      <aside className="hidden md:block">
        <div className="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </aside>

      {drawerOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 bg-black/30"
          />
          <div className="absolute inset-y-0 left-0 shadow-md">
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={() => setDrawerOpen(true)} />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  );
}
