import { useMemo, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { sandboxApi } from "@shared/api/sandbox";
import { LangPicker } from "@shared/components/LangPicker";
import type {
  SandboxAutoPlayMode,
  SandboxTimingPreset,
} from "@shared/api/sandbox";

import { ROLE_CODES, ROLE_EMOJI } from "@shared/constants/roles";
import { RoleDistributionPreview } from "../components/sandbox/RoleDistributionPreview";
import "../components/sandbox/sandbox.css";

// All roles enabled by default — mirrors backend DEFAULT_ROLES_ENABLED.
const DEFAULT_ROLES: Record<string, boolean> = Object.fromEntries(
  ROLE_CODES.map((code) => [code, true]),
);

const ROLE_GROUPS: Array<{ labelKey: string; keys: string[] }> = [
  {
    labelKey: "admin.sandbox.team_citizens",
    keys: [
      "citizen",
      "detective",
      "sergeant",
      "mayor",
      "doctor",
      "hooker",
      "hobo",
      "lucky",
      "suicide",
      "kamikaze",
    ],
  },
  {
    labelKey: "admin.sandbox.team_mafia",
    keys: ["don", "mafia", "lawyer", "journalist", "killer"],
  },
  {
    labelKey: "admin.sandbox.team_singletons",
    keys: ["maniac", "werewolf", "mage", "arsonist", "crook", "snitch"],
  },
];

const AUTO_MODES: SandboxAutoPlayMode[] = ["paused", "auto", "random_actions"];
const TIMINGS: SandboxTimingPreset[] = ["fast", "normal", "slow", "manual"];

export function SandboxCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [nPlayers, setNPlayers] = useState(8);
  const [mafiaRatio, setMafiaRatio] = useState<"low" | "high">("low");
  const [autoMode, setAutoMode] = useState<SandboxAutoPlayMode>("paused");
  const [timing, setTiming] = useState<SandboxTimingPreset>("fast");
  const [language, setLanguage] = useState<"uz" | "ru" | "en">("uz");
  const [seed, setSeed] = useState<string>("");
  const [startNow, setStartNow] = useState(true);
  const [roles, setRoles] = useState<Record<string, boolean>>(DEFAULT_ROLES);
  // null → use the default distribution algorithm; otherwise an exact
  // length-N roster dealt out verbatim (mirrors the group role_distribution
  // override). Kept in sync with nPlayers so it's always a valid length.
  const [customRoster, setCustomRoster] = useState<string[] | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const changeNPlayers = (n: number) => {
    setNPlayers(n);
    setCustomRoster((prev) => {
      if (prev === null) return null;
      const next = prev.slice(0, n);
      while (next.length < n) next.push("citizen");
      return next;
    });
  };

  const enableRoster = () => {
    const seed = ["don", "detective"];
    while (seed.length < nPlayers) seed.push("citizen");
    setCustomRoster(seed);
  };

  const updateRosterSlot = (index: number, role: string) =>
    setCustomRoster((prev) => {
      if (prev === null) return prev;
      const copy = [...prev];
      copy[index] = role;
      return copy;
    });

  const createMutation = useMutation({
    mutationFn: sandboxApi.create,
    onSuccess: (data) => navigate(`/admin/sandbox/${data.sandbox_id}`),
    onError: (err: Error) =>
      setSubmitError(err.message || t("admin.sandbox.errors.create_failed")),
  });

  const toggleRole = (code: string) =>
    setRoles((prev) => ({ ...prev, [code]: !prev[code] }));

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    createMutation.mutate({
      n_players: nPlayers,
      mafia_ratio: mafiaRatio,
      auto_play_mode: autoMode,
      timing_preset: timing,
      language,
      seed: seed.trim() ? parseInt(seed, 10) : undefined,
      roles_enabled: roles,
      role_distribution:
        customRoster && customRoster.length === nPlayers
          ? { [String(nPlayers)]: customRoster }
          : undefined,
      start_immediately: startNow,
    });
  };

  const previewProps = useMemo(
    () => ({ nPlayers, mafiaRatio, enabled: roles }),
    [nPlayers, mafiaRatio, roles],
  );

  const mafiaPreviewCount =
    mafiaRatio === "high"
      ? Math.max(1, Math.floor(nPlayers / 3))
      : Math.max(1, Math.floor(nPlayers / 4));

  return (
    <>
      <div className="sb-list-header">
        <h1 className="admin-page-title" style={{ margin: 0 }}>
          🧪 {t("admin.sandbox.create.title")}
        </h1>
        <Link to="/admin/sandbox" className="admin-btn">
          ← {t("admin.sandbox.create.back_to_list")}
        </Link>
      </div>

      <form onSubmit={onSubmit} style={{ display: "grid", gap: "1rem" }}>
        <div className="sb-create-grid">
          {/* --- Left: numeric / mode inputs --- */}
          <div className="admin-card">
            <h3 style={{ marginTop: 0 }}>{t("admin.sandbox.create.basics")}</h3>

            <label className="sb-form-label">
              {t("admin.sandbox.create.player_count")}: <strong>{nPlayers}</strong>
              <input
                type="range"
                min={4}
                max={30}
                value={nPlayers}
                onChange={(e) => changeNPlayers(parseInt(e.target.value, 10))}
                style={{ width: "100%" }}
              />
            </label>

            <label className="sb-form-label">
              {t("admin.sandbox.create.mafia_ratio")}:{" "}
              <select
                value={mafiaRatio}
                onChange={(e) => setMafiaRatio(e.target.value as "low" | "high")}
                className="admin-input"
                style={{ marginLeft: "0.5rem", width: "auto" }}
              >
                <option value="low">{t("admin.sandbox.create.ratio_low")}</option>
                <option value="high">{t("admin.sandbox.create.ratio_high")}</option>
              </select>
              <span style={{ color: "var(--muted)", marginLeft: "0.5rem" }}>
                →{" "}
                {t("admin.sandbox.create.n_mafia", {
                  count: mafiaPreviewCount,
                })}
              </span>
            </label>

            <label className="sb-form-label">
              {t("admin.sandbox.create.timing")}:
              <select
                value={timing}
                onChange={(e) => setTiming(e.target.value as SandboxTimingPreset)}
                className="admin-input"
                style={{ marginLeft: "0.5rem", width: "auto" }}
              >
                {TIMINGS.map((v) => (
                  <option key={v} value={v}>
                    {t(`admin.sandbox.create.timing_${v}`)}
                  </option>
                ))}
              </select>
              <div className="sb-form-hint">
                {t(`admin.sandbox.create.timing_${timing}_hint`)}
              </div>
            </label>

            <label className="sb-form-label">
              {t("admin.sandbox.create.auto_play")}:
              <select
                value={autoMode}
                onChange={(e) => setAutoMode(e.target.value as SandboxAutoPlayMode)}
                className="admin-input"
                style={{ marginLeft: "0.5rem", width: "auto" }}
              >
                {AUTO_MODES.map((v) => (
                  <option key={v} value={v}>
                    {t(`admin.sandbox.create.auto_${v}`)}
                  </option>
                ))}
              </select>
              <div className="sb-form-hint">
                {t(`admin.sandbox.create.auto_${autoMode}_hint`)}
              </div>
            </label>

            <label className="sb-form-label">
              {t("admin.sandbox.create.language")}:
              <LangPicker
                value={language}
                onChange={(code) => setLanguage(code as "uz" | "ru" | "en")}
                style={{ marginLeft: "0.5rem" }}
              />
            </label>

            <label className="sb-form-label">
              {t("admin.sandbox.create.seed")}:
              <input
                type="text"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                placeholder={t("admin.sandbox.create.seed_placeholder")}
                className="admin-input"
                style={{ marginLeft: "0.5rem", width: "10rem" }}
              />
            </label>

            <label className="sb-form-inline">
              <input
                type="checkbox"
                checked={startNow}
                onChange={(e) => setStartNow(e.target.checked)}
              />
              <span>{t("admin.sandbox.create.start_now")}</span>
            </label>
          </div>

          {/* --- Right: distribution preview --- */}
          <div>
            <RoleDistributionPreview {...previewProps} />
          </div>
        </div>

        {/* --- Roles enabled --- */}
        <div className="admin-card">
          <h3 style={{ marginTop: 0 }}>{t("admin.sandbox.create.roles")}</h3>
          <div className="sb-roles-grid">
            {ROLE_GROUPS.map((group) => (
              <div key={group.labelKey}>
                <span className="sb-role-group-label">{t(group.labelKey)}</span>
                <div>
                  {group.keys.map((code) => (
                    <label
                      key={code}
                      className={`sb-role-toggle ${roles[code] ? "" : "off"}`}
                    >
                      <input
                        type="checkbox"
                        checked={!!roles[code]}
                        onChange={() => toggleRole(code)}
                      />
                      <span>
                        {ROLE_EMOJI[code] || "❓"} {code}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* --- Role distribution override (this N) --- */}
        <div className="admin-card">
          <h3 style={{ marginTop: 0 }}>
            {t("admin.sandbox.create.distribution")} ({nPlayers})
          </h3>
          {customRoster === null ? (
            <>
              <p className="sb-form-hint" style={{ marginTop: 0 }}>
                {t("admin.sandbox.create.distribution_using_algorithm")}
              </p>
              <button type="button" className="admin-btn" onClick={enableRoster}>
                {t("admin.sandbox.create.distribution_override")}
              </button>
            </>
          ) : (
            <>
              <p className="sb-form-hint" style={{ marginTop: 0 }}>
                {t("admin.sandbox.create.distribution_slots_hint", { n: nPlayers })}
              </p>
              <div className="sb-roles-grid">
                {customRoster.map((roleCode, idx) => (
                  <label key={idx} className="sb-form-label" style={{ margin: 0 }}>
                    #{idx + 1}
                    <select
                      value={roleCode}
                      onChange={(e) => updateRosterSlot(idx, e.target.value)}
                      className="admin-input"
                      style={{ marginLeft: "0.5rem", width: "auto" }}
                    >
                      {ROLE_CODES.map((code) => (
                        <option key={code} value={code}>
                          {ROLE_EMOJI[code]} {code}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
              <button
                type="button"
                className="admin-btn"
                style={{ marginTop: "0.75rem" }}
                onClick={() => setCustomRoster(null)}
              >
                {t("admin.sandbox.create.distribution_reset")}
              </button>
            </>
          )}
        </div>

        {/* --- Submit row --- */}
        {submitError && (
          <div className="sb-error-banner">⚠️ {submitError}</div>
        )}
        <div className="sb-create-actions">
          <Link to="/admin/sandbox" className="admin-btn">
            {t("admin.sandbox.create.cancel")}
          </Link>
          <button
            type="submit"
            className="admin-btn primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending
              ? `⏳ ${t("admin.sandbox.create.creating")}`
              : startNow
                ? `🚀 ${t("admin.sandbox.create.submit_and_start")}`
                : `+ ${t("admin.sandbox.create.submit")}`}
          </button>
        </div>
      </form>
    </>
  );
}
