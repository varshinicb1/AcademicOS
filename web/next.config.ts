import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

/**
 * Phase 2 of the web-client migration: the shell and the design system.
 * See docs/frontend-platform-decision.md.
 *
 * `transpilePackages` is not used and there is no UI framework dependency
 * yet, deliberately. The design system in docs/design-system.md is fully
 * specified and token-driven, so adopting shadcn/ui now would introduce a
 * second set of conventions for an agent to drift against. Radix primitives
 * (dialog, select, combobox) are the Phase 3 addition, where accessible
 * overlays are genuinely hard to write by hand.
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,

  // Turbopack walks up looking for a workspace root and finds an unrelated
  // package-lock.json in the user's home directory, which it then warns about
  // and refuses to use. Pinning the root to web/ removes the warning, which
  // matters because a persistent warning is where real ones go to hide.
  turbopack: { root: here },

  // The API base URL is baked at build time, exactly as the Flutter client did.
  // The GCP release serves the SPA same-origin, so `/api/v1` is the default.
  env: {
    NEXT_PUBLIC_ACADEMICOS_API:
      process.env.NEXT_PUBLIC_ACADEMICOS_API ?? "/api/v1",
  },
};

export default nextConfig;
