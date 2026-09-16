/**
 * Minimal class-name joiner.
 *
 * Deliberately not `clsx` or `tailwind-merge`: Phase 2 has no UI dependencies,
 * and adding one to concatenate strings would be the first step towards a
 * second styling vocabulary that the design-token checker cannot police.
 */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
