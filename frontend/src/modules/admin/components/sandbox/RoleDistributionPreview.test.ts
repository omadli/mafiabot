/**
 * Smoke tests for the role-distribution preview math.
 *
 * Mirror of `backend/tests/unit/test_distribution.py` — any divergence
 * here means the preview lies to the user. Kept narrow on purpose: we
 * verify thresholds + slot counts, not the exact random-shuffle output.
 */
import { describe, expect, it } from "vitest";

import { computePreview } from "./RoleDistributionPreview";

const ALL_ON: Record<string, boolean> = {
  citizen: true,
  detective: true,
  sergeant: true,
  mayor: true,
  doctor: true,
  hooker: true,
  hobo: true,
  lucky: true,
  suicide: true,
  kamikaze: true,
  don: true,
  mafia: true,
  lawyer: true,
  journalist: true,
  killer: true,
  maniac: true,
  werewolf: true,
  mage: true,
  arsonist: true,
  crook: true,
  snitch: true,
};

describe("computePreview", () => {
  it("low ratio at N=8 → 2 mafia, no singletons (n<8 boundary), citizens fill", () => {
    const p = computePreview(8, "low", ALL_ON);
    expect(p.mafia.length).toBe(2);
    expect(p.mafia[0]).toBe("don");
    // n=8 → target_singletons = max(1, 8//4) = 2
    expect(p.singletons.length).toBe(2);
    const total = p.mafia.length + p.singletons.length + p.civilians.length;
    expect(total).toBe(8);
  });

  it("lawyer appears at N>=12 (low ratio, all enabled)", () => {
    const below = computePreview(11, "low", ALL_ON);
    expect(below.mafia.includes("lawyer")).toBe(false);
    const at = computePreview(12, "low", ALL_ON);
    expect(at.mafia.includes("lawyer")).toBe(true);
  });

  it("journalist appears at N>=17 (low ratio, all enabled)", () => {
    const below = computePreview(16, "low", ALL_ON);
    expect(below.mafia.includes("journalist")).toBe(false);
    const at = computePreview(17, "low", ALL_ON);
    expect(at.mafia.includes("journalist")).toBe(true);
  });

  it("killer appears at N>=25 (high ratio)", () => {
    const below = computePreview(24, "high", ALL_ON);
    expect(below.mafia.includes("killer")).toBe(false);
    const at = computePreview(25, "high", ALL_ON);
    expect(at.mafia.includes("killer")).toBe(true);
  });

  it("no singletons below N=8", () => {
    const p = computePreview(7, "low", ALL_ON);
    expect(p.singletons.length).toBe(0);
  });

  it("respects disabled roles in mafia slot allocation", () => {
    const enabled = { ...ALL_ON, lawyer: false };
    const p = computePreview(12, "low", enabled);
    expect(p.mafia.includes("lawyer")).toBe(false);
    // Slot is filled with plain mafia instead.
    expect(p.mafia.filter((r) => r === "mafia").length).toBeGreaterThanOrEqual(1);
  });

  it("N=30 high ratio fills 10 mafia / 7 singletons / 13 civilians", () => {
    const p = computePreview(30, "high", ALL_ON);
    expect(p.mafia.length).toBe(10);
    expect(p.singletons.length).toBe(7);
    expect(p.civilians.length).toBe(13);
  });

  it("totals always equal nPlayers", () => {
    for (const n of [4, 5, 6, 8, 10, 12, 15, 18, 20, 24, 27, 30]) {
      for (const ratio of ["low", "high"] as const) {
        const p = computePreview(n, ratio, ALL_ON);
        const total = p.mafia.length + p.singletons.length + p.civilians.length;
        expect(total, `N=${n}/${ratio}`).toBe(n);
      }
    }
  });
});
