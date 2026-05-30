/**
 * Surface-agnostic context for shared super-admin pages.
 *
 * The same React components mount in two different shells:
 *
 *   - `/admin/*`     — website with login/password (JWT)
 *   - `/webapp/sa/*` — Telegram Mini App with initData
 *
 * They render the same data and call the same API but differ in two
 * mechanical ways: the URL prefix to use when linking between SA pages
 * and (optionally) the visual surface for class-based styling. Pages
 * read those from `useSa()` instead of hardcoding `/admin` or `/webapp/sa`
 * literals so the same source file works on either shell.
 */

import { createContext, useContext, type ReactNode } from "react";

import "./styles.css";

export type SaSurface = "admin" | "webapp";

interface SaContextValue {
  /** URL prefix for all SA routes — e.g. "/admin" or "/webapp/sa". */
  basePath: string;
  /** Visual surface — pages may pick CSS class sets accordingly. */
  surface: SaSurface;
}

const SaContext = createContext<SaContextValue | null>(null);

interface SaProviderProps extends SaContextValue {
  children: ReactNode;
}

export function SaProvider({ basePath, surface, children }: SaProviderProps) {
  return (
    <SaContext.Provider value={{ basePath, surface }}>{children}</SaContext.Provider>
  );
}

/**
 * Read the active SA context. Throws if a page outside the provider tries
 * to use it — that's a wiring mistake, not a runtime branch worth handling.
 */
export function useSa(): SaContextValue {
  const ctx = useContext(SaContext);
  if (ctx === null) {
    throw new Error("useSa() must be used inside <SaProvider>");
  }
  return ctx;
}

/**
 * Build a path under the current SA surface. Usage:
 *
 *     const userPath = useSaPath(`/users/${userId}`);
 *     <Link to={userPath}>…</Link>
 */
export function useSaPath(suffix: string): string {
  const { basePath } = useSa();
  return suffix.startsWith("/") ? `${basePath}${suffix}` : `${basePath}/${suffix}`;
}
