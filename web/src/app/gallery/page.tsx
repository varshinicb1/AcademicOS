"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { PageHeader } from "@/components/shell";
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  Column,
  DataTable,
  EmptyState,
  KpiTile,
  Skeleton,
  SkeletonText,
  Status,
  StatusPill,
  Tabs,
} from "@/components/ui";

function Section({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <section className="mb-8" data-testid={`section-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      {note ? <p className="mt-0.5 mb-3 text-sm text-body">{note}</p> : <div className="mb-3" />}
      {children}
    </section>
  );
}

const SWATCHES = [
  "var(--color-surface-canvas)",
  "var(--color-surface-card)",
  "var(--color-surface-inset)",
  "var(--color-neutral-200)",
  "var(--color-neutral-300)",
  "var(--color-neutral-400)",
  "var(--color-neutral-600)",
  "var(--color-neutral-900)",
  "var(--color-brand-50)",
  "var(--color-brand-600)",
  "var(--color-brand-700)",
  "var(--color-success-fg)",
  "var(--color-warning-fg)",
  "var(--color-danger-fg)",
  "var(--color-info-fg)",
];

type Row = { id: string; name: string; className: string; score: number; status: Status };

const ROWS: Row[] = [
  { id: "1", name: "Aarav Menon", className: "10-B", score: 92, status: "completed" },
  { id: "2", name: "Diya Rao", className: "10-B", score: 78, status: "on-pace" },
  { id: "3", name: "Ishaan Gupta", className: "10-A", score: 54, status: "at-risk" },
  { id: "4", name: "Meera Nair", className: "10-A", score: 41, status: "overdue" },
  { id: "5", name: "Rohan Das", className: "10-C", score: 0, status: "skipped" },
];

const COLUMNS: Array<Column<Row>> = [
  { key: "name", header: "Student", cell: (r) => <span className="text-ink">{r.name}</span> },
  { key: "class", header: "Class", cell: (r) => r.className },
  { key: "score", header: "Score", align: "right", cell: (r) => `${r.score}%` },
  { key: "status", header: "Status", cell: (r) => <StatusPill status={r.status} data-testid={`row-status-${r.id}`} /> },
];

export default function GalleryPage() {
  const [tab, setTab] = useState("overview");

  return (
    <>
      <PageHeader
        title="Component gallery"
        description="Every primitive in every state, rendered from design/tokens.json. This page is the review surface: if a token changes, the effect is visible here before it reaches a screen."
        breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Component gallery" }]}
        data-testid="gallery-header"
      />

      <Section title="Type scale" note="Paired size and line-height, from --text-* and --leading-*.">
        <Card>
          <CardBody className="space-y-1">
            <div className="text-3xl font-semibold text-ink">3xl 30/36 Heading</div>
            <div className="text-2xl font-semibold text-ink">2xl 24/30 Heading</div>
            <div className="text-xl font-semibold text-ink">xl 20/28 Heading</div>
            <div className="text-lg font-medium text-ink">lg 16/24 Subheading</div>
            <div className="text-base text-ink">base 14/20 Body ink</div>
            <div className="text-sm text-body">sm 13/18 Body secondary</div>
            <div className="text-xs text-muted">xs 12/16 Caption and label</div>
            <div className="text-2xs text-muted">2xs 11/14 Overline</div>
            <div className="tabular text-base text-ink">Tabular: 1,234,567.89</div>
          </CardBody>
        </Card>
      </Section>

      <Section title="Colours" note="Tokens only. A raw hex anywhere under web/ fails scripts/check_design_tokens.py.">
        <div className="grid grid-cols-5 gap-2 sm:grid-cols-8">
          {SWATCHES.map((v) => (
            <div key={v} className="rounded-md border border-line bg-card p-1.5">
              <div className="h-10 rounded-sm border border-line" style={{ background: v }} />
              <div className="mt-1 truncate text-2xs text-muted" title={v}>
                {v.replace("var(--", "").replace(")", "")}
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Buttons"
        note="Full state matrix: default, hover, active, focus, disabled, loading. Hover and active need a real pointer; focus is Tab."
      >
        <Card>
          <CardBody className="space-y-4">
            <Row label="primary">
              <Button data-testid="btn-primary">Generate paper</Button>
              <Button data-testid="btn-primary-disabled" disabled>
                Generate paper
              </Button>
              <Button data-testid="btn-primary-loading" loading>
                Generate paper
              </Button>
            </Row>
            <Row label="secondary">
              <Button variant="secondary" data-testid="btn-secondary">
                Export
              </Button>
              <Button variant="secondary" disabled data-testid="btn-secondary-disabled">
                Export
              </Button>
              <Button variant="secondary" loading data-testid="btn-secondary-loading">
                Export
              </Button>
            </Row>
            <Row label="ghost">
              <Button variant="ghost" data-testid="btn-ghost">
                Cancel
              </Button>
              <Button variant="ghost" disabled data-testid="btn-ghost-disabled">
                Cancel
              </Button>
            </Row>
            <Row label="danger">
              <Button variant="danger" data-testid="btn-danger">
                Delete paper
              </Button>
              <Button variant="danger" disabled data-testid="btn-danger-disabled">
                Delete paper
              </Button>
            </Row>
            <Row label="sizes">
              <Button size="sm" data-testid="btn-sm">
                Small
              </Button>
              <Button size="md" data-testid="btn-md">
                Medium
              </Button>
              <Button size="lg" data-testid="btn-lg">
                Large
              </Button>
            </Row>
          </CardBody>
        </Card>
      </Section>

      <Section title="Status pills" note="Colour is never the only signal, so a label and a glyph are always present.">
        <div className="flex flex-wrap gap-2">
          {(["completed", "on-pace", "at-risk", "overdue", "scheduled", "skipped"] as Status[]).map((s) => (
            <StatusPill key={s} status={s} data-testid={`pill-${s}`} />
          ))}
          <StatusPill status="overdue" label="Overdue by 3 days" data-testid="pill-overdue-custom" />
        </div>
      </Section>

      <Section title="KPI tiles" note="Values are tabular; deltas carry a direction and a spoken label.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <KpiTile
            data-testid="kpi-coverage"
            label="Syllabus coverage"
            value="78.4"
            unit="%"
            delta={{ direction: "up", value: "4.1%", tone: "good" }}
            deltaLabel="up 4.1 percent against last month"
          />
          <KpiTile
            data-testid="kpi-papers"
            label="Papers generated"
            value="1,204"
            delta={{ direction: "up", value: "82", tone: "good" }}
            deltaLabel="up 82 against last month"
          />
          <KpiTile
            data-testid="kpi-at-risk"
            label="Students at risk"
            value="37"
            delta={{ direction: "down", value: "6", tone: "bad" }}
            deltaLabel="up 6 against last month"
          />
          <KpiTile
            data-testid="kpi-pending"
            label="Awaiting review"
            value="12"
            delta={{ direction: "flat", value: "no change", tone: "neutral" }}
          />
        </div>
      </Section>

      <Section title="Cards">
        <div className="grid gap-3 lg:grid-cols-2">
          <Card data-testid="card-basic">
            <CardHeader
              title="Coverage by subject"
              description="Grade 10, term 1"
              actions={
                <Button variant="ghost" size="sm" data-testid="card-action">
                  View
                </Button>
              }
            />
            <CardBody>
              <SkeletonText lines={3} />
            </CardBody>
          </Card>
          <Card data-testid="card-plain">
            <CardBody>
              <p className="text-sm text-body">
                A card with no header. Cards are the only elevation-1 surface in the product and are never
                nested.
              </p>
            </CardBody>
          </Card>
        </div>
      </Section>

      <Section title="Data table" note="Populated, loading and empty. Rows are presentational; the page owns sorting and paging.">
        <Card className="mb-3">
          <DataTable
            data-testid="table-populated"
            columns={COLUMNS}
            rows={ROWS}
            rowKey={(r) => r.id}
            empty={<EmptyState title="No students" description="Nothing to show." />}
          />
        </Card>
        <Card className="mb-3">
          <DataTable
            data-testid="table-loading"
            columns={COLUMNS}
            rows={[]}
            rowKey={(r) => r.id}
            loading
            skeletonRows={3}
            empty={<EmptyState title="No students" description="Nothing to show." />}
          />
        </Card>
        <Card>
          <DataTable
            data-testid="table-empty"
            columns={COLUMNS}
            rows={[]}
            rowKey={(r) => r.id}
            empty={
              <EmptyState
                data-testid="table-empty-state"
                title="No students enrolled"
                description="Enrol a student in this class to see them here."
                action={<Button data-testid="table-empty-action">Enrol student</Button>}
              />
            }
          />
        </Card>
      </Section>

      <Section title="Tabs" note="Arrow keys move between tabs; Home and End jump to the ends.">
        <Card>
          <CardBody>
            <Tabs
              data-testid="gallery-tabs"
              value={tab}
              onChange={setTab}
              tabs={[
                { id: "overview", label: "Overview" },
                { id: "topics", label: "Topics" },
                { id: "history", label: "History" },
                { id: "disabled", label: "Archive" },
              ]}
              panels={{
                overview: <p className="text-sm text-body">Overview panel. Only the active panel is mounted.</p>,
                topics: <p className="text-sm text-body">Topics panel.</p>,
                history: <p className="text-sm text-body">History panel.</p>,
                disabled: <p className="text-sm text-body">Archive panel.</p>,
              }}
            />
          </CardBody>
        </Card>
      </Section>

      <Section title="Skeletons" note="Reserved space, so nothing shifts when data arrives.">
        <Card>
          <CardBody className="space-y-4">
            <Skeleton className="h-4 w-1/3" data-testid="skeleton-block" />
            <SkeletonText lines={4} />
          </CardBody>
        </Card>
      </Section>
    </>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="w-20 shrink-0 text-xs text-muted">{label}</div>
      <div className="flex flex-wrap items-center gap-2">{children}</div>
    </div>
  );
}
