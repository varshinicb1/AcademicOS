import type { IconName } from "@/components/ui/icon";

/**
 * Navigation, derived from the modules that actually exist in
 * contract/openapi.json -- not from a designer's idea of a school product.
 * Every `href` below corresponds to a real backend module, and Phase 3 creates
 * the route that renders it.
 *
 * Routes that do not exist yet are still declared. A nav that grows as screens
 * land is a nav that gets restructured twice; this way the information
 * architecture is fixed up front and Phase 3 fills it in.
 */
export interface NavItem {
  href: string;
  label: string;
  icon: IconName;
  /** Backend module this screen is built on, for traceability back to the contract. */
  module: string;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export const NAV: NavSection[] = [
  {
    label: "Overview",
    items: [
      { href: "/", label: "Dashboard", icon: "dashboard", module: "insights" },
    ],
  },
  {
    label: "Academics",
    items: [
      { href: "/curriculum", label: "Curriculum", icon: "curriculum", module: "curriculum" },
      { href: "/questions", label: "Question bank", icon: "question", module: "questions" },
    ],
  },
  {
    label: "Paperwork",
    items: [
      { href: "/papers", label: "Papers", icon: "papers", module: "papers" },
      { href: "/assessments", label: "Assessments", icon: "assessments", module: "assessments" },
      { href: "/practice", label: "Practice", icon: "practice", module: "practice" },
    ],
  },
  {
    label: "Grading",
    items: [
      { href: "/scan", label: "Scan", icon: "scan", module: "scan" },
      { href: "/evaluations", label: "Evaluations", icon: "evaluations", module: "evaluations" },
      { href: "/insights", label: "Insights", icon: "insights", module: "insights" },
    ],
  },
  {
    label: "Administration",
    items: [
      { href: "/schools", label: "Schools", icon: "schools", module: "schools" },
      { href: "/users", label: "Users", icon: "users", module: "auth" },
      { href: "/consent", label: "Consent", icon: "consent", module: "consent" },
    ],
  },
  {
    // Development surface, kept out of the way rather than deleted: it is how a
    // reviewer confirms the primitives still render correctly after a token
    // change. Remove this section when the product ships.
    label: "Design",
    items: [
      { href: "/gallery", label: "Component gallery", icon: "gallery", module: "n/a" },
    ],
  },
];
