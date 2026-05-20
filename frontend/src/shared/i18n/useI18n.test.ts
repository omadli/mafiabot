import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";

import { useI18n } from "./useI18n";

describe("useI18n flat-key mapping", () => {
  it("translates a flat key into its nested target", () => {
    const { result } = renderHook(() => useI18n());
    // sa-nav-dashboard → sa.nav.dashboard which is "Dashboard" in uz
    expect(result.current.t("sa-nav-dashboard")).toBeTypeOf("string");
    expect(result.current.t("sa-nav-dashboard")).not.toBe("sa-nav-dashboard");
  });

  it("falls back to provided default when key is unmapped and missing", () => {
    const { result } = renderHook(() => useI18n());
    expect(result.current.t("unknown-key-12345", "fallback-value")).toBe(
      "fallback-value",
    );
  });

  it("exposes current locale", () => {
    const { result } = renderHook(() => useI18n());
    expect(["uz", "ru", "en"]).toContain(result.current.locale);
  });

  it("setLocale swaps the language", () => {
    const { result, rerender } = renderHook(() => useI18n());
    result.current.setLocale("en");
    rerender();
    expect(result.current.locale).toBe("en");
    // Restore to default for other tests
    result.current.setLocale("uz");
  });
});
