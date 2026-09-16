import Link from "next/link";
import { PageHeader } from "@/components/shell";
import { buttonClasses, EmptyState } from "@/components/ui";

export default function Page() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Phase 2 delivered the shell and the component primitives. The screens themselves are Phase 3, and will be built on the frozen contract in contract/openapi.json."
        data-testid="dashboard-header"
      />

      <div className="rounded-lg border border-line bg-card shadow-sm">
        <EmptyState
          data-testid="dashboard-empty"
          title="No data yet"
          description="This screen is a seam, not a feature. It renders the shell so Phase 3 can port the dashboard onto a layout that is already proven."
          action={
            <Link
              href="/gallery"
              data-testid="dashboard-goto-gallery"
              className={buttonClasses({ variant: "primary" })}
            >
              Open component gallery
            </Link>
          }
        />
      </div>
    </>
  );
}
