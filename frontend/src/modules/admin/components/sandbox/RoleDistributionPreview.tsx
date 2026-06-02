/**
 * Live preview of the Mafia / Singleton / Civilian split given the
 * current sandbox-create form values.
 *
 * Mirrors `backend/app/core/distribution.py`. Keep in sync — drift here
 * means the preview lies. The numbers are estimates: actual role
 * assignment is shuffled at game start.
 */
import { useTranslation } from "react-i18next";

import { ROLE_EMOJI } from "@shared/constants/roles";

// Mirror of MAFIA_PRIORITY in distribution.py (must stay in sync).
const MAFIA_PRIORITY: Array<[string, number]> = [
  ["lawyer", 12],
  ["journalist", 17],
  ["killer", 25],
];

const CIVILIAN_PRIORITY: Array<[string, number]> = [
  ["detective", 4],
  ["doctor", 5],
  ["hooker", 6],
  ["sergeant", 8],
  ["mayor", 10],
  ["hobo", 12],
  ["lucky", 14],
];

const SINGLETON_MULTI: Array<[string, number]> = [
  ["werewolf", 24],
  ["maniac", 28],
];

const SINGLETON_ROLES = [
  "suicide",
  "maniac",
  "werewolf",
  "mage",
  "arsonist",
  "crook",
  "snitch",
];

interface Preview {
  mafia: string[];
  civilians: string[];
  singletons: string[];
}

export function computePreview(
  nPlayers: number,
  mafiaRatio: "low" | "high",
  enabled: Record<string, boolean>,
): Preview {
  const n = nPlayers;
  const mafiaCount =
    mafiaRatio === "high" ? Math.max(1, Math.floor(n / 3)) : Math.max(1, Math.floor(n / 4));

  const mafia: string[] = ["don"];
  for (const [code, threshold] of MAFIA_PRIORITY) {
    if (mafia.length >= mafiaCount) break;
    if (n >= threshold && enabled[code]) mafia.push(code);
  }
  while (mafia.length < mafiaCount) mafia.push("mafia");

  const targetSingletons = n >= 8 ? Math.max(1, Math.floor(n / 4)) : 0;
  const availableSingletons = SINGLETON_ROLES.filter((r) => enabled[r]);
  const singletons: string[] = [];
  if (availableSingletons.length > 0 && targetSingletons > 0) {
    const pool = [...availableSingletons].slice(0, targetSingletons);
    singletons.push(...pool);
    for (const [role, threshold] of SINGLETON_MULTI) {
      if (n >= threshold && singletons.includes(role) && singletons.length < targetSingletons) {
        singletons.push(role);
      }
    }
    while (singletons.length < targetSingletons && pool.length > 0) {
      singletons.push(pool[singletons.length % pool.length]);
    }
  }

  const civilianCount = Math.max(0, n - mafia.length - singletons.length);
  const civilians: string[] = [];
  if (enabled.detective && civilianCount > 0) civilians.push("detective");
  for (const [code, threshold] of CIVILIAN_PRIORITY.slice(1)) {
    if (civilians.length >= civilianCount) break;
    if (n >= threshold && enabled[code]) civilians.push(code);
  }
  if (
    n >= 20 &&
    enabled.sergeant &&
    civilians.filter((c) => c === "sergeant").length < 2 &&
    civilians.length < civilianCount
  ) {
    civilians.push("sergeant");
  }
  if (n >= 18 && enabled.kamikaze) {
    const kCount = Math.ceil(n / 10);
    for (let i = 0; i < kCount && civilians.length < civilianCount; i++) {
      civilians.push("kamikaze");
    }
  }
  while (civilians.length < civilianCount) civilians.push("citizen");
  if (civilians.length > civilianCount) civilians.length = civilianCount;

  return { mafia, civilians, singletons };
}

function RoleChip({ role }: { role: string }) {
  return (
    <span className="sb-preview-chip" title={role}>
      {ROLE_EMOJI[role] || "❓"} {role}
    </span>
  );
}

interface Props {
  nPlayers: number;
  mafiaRatio: "low" | "high";
  enabled: Record<string, boolean>;
}

export function RoleDistributionPreview({ nPlayers, mafiaRatio, enabled }: Props) {
  const { t } = useTranslation();
  const preview = computePreview(nPlayers, mafiaRatio, enabled);
  const total = preview.mafia.length + preview.singletons.length + preview.civilians.length;

  return (
    <div className="admin-card sb-preview-card">
      <div className="sb-preview-header">
        <strong>{t("admin.sandbox.create.distribution_preview")}</strong>
        <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
          {t("admin.sandbox.create.placed_of_total", {
            placed: total,
            total: nPlayers,
          })}
        </span>
      </div>
      <div className="sb-preview-row">
        <strong className="sb-preview-team-mafia">
          🤵 {t("admin.sandbox.team_mafia")} ({preview.mafia.length})
        </strong>
        <div style={{ marginTop: "0.25rem" }}>
          {preview.mafia.map((r, i) => (
            <RoleChip key={`m-${i}`} role={r} />
          ))}
        </div>
      </div>
      <div className="sb-preview-row">
        <strong className="sb-preview-team-singleton">
          🃏 {t("admin.sandbox.team_singletons")} ({preview.singletons.length})
        </strong>
        <div style={{ marginTop: "0.25rem" }}>
          {preview.singletons.length === 0 ? (
            <span style={{ color: "var(--muted)" }}>
              {t("admin.sandbox.create.none")}
            </span>
          ) : (
            preview.singletons.map((r, i) => <RoleChip key={`s-${i}`} role={r} />)
          )}
        </div>
      </div>
      <div className="sb-preview-row">
        <strong className="sb-preview-team-civilian">
          👨 {t("admin.sandbox.team_citizens")} ({preview.civilians.length})
        </strong>
        <div style={{ marginTop: "0.25rem" }}>
          {preview.civilians.map((r, i) => (
            <RoleChip key={`c-${i}`} role={r} />
          ))}
        </div>
      </div>
    </div>
  );
}
