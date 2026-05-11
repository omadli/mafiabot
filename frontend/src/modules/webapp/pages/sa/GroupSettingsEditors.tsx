/**
 * Inline editors for each section of a group's GroupSettings.
 *
 * Each editor is presentational + delegates mutations to a single onSave(section, value)
 * callback supplied by the parent (SaGroupDetailPage). Optimistic UI: the
 * UI updates immediately on click; the parent's react-query mutation
 * invalidates and refetches.
 */

import { useTranslation } from "react-i18next";

import type { GroupSettings } from "@shared/api/sa";

interface EditorProps {
  settings: GroupSettings;
  onSave: (section: string, value: unknown) => void;
}

// === Role groups (matches backend ROLE_GROUPS) ===

const ROLE_GROUPS: { team: string; codes: string[] }[] = [
  {
    team: "civilians",
    codes: [
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
  { team: "mafia", codes: ["don", "mafia", "lawyer", "journalist", "killer"] },
  { team: "singletons", codes: ["maniac", "werewolf", "mage", "arsonist", "crook", "snitch"] },
];

const ROLE_EMOJI: Record<string, string> = {
  citizen: "👨🏼",
  detective: "🕵🏻‍♂",
  sergeant: "👮🏻‍♂",
  mayor: "🎖",
  doctor: "👨🏻‍⚕",
  hooker: "💃",
  hobo: "🧙‍♂",
  lucky: "🤞🏼",
  suicide: "🤦🏼",
  kamikaze: "💣",
  don: "🤵🏻",
  mafia: "🤵🏼",
  lawyer: "👨‍💼",
  journalist: "👩🏼‍💻",
  killer: "🥷",
  maniac: "🔪",
  werewolf: "🐺",
  mage: "🧙",
  arsonist: "🧟",
  crook: "🤹",
  snitch: "🤓",
};

// === Roles editor ===

export function RolesEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
  const roles = settings.roles || {};

  const toggle = (code: string) => {
    const next = { ...roles, [code]: !roles[code] };
    onSave("roles", next);
  };

  return (
    <div>
      {ROLE_GROUPS.map((group) => (
        <div key={group.team} style={{ marginBottom: "1rem" }}>
          <h4 style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0.5rem 0" }}>
            {t(`admin.settings.team_${group.team}`)}
          </h4>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
              gap: "0.4rem",
            }}
          >
            {group.codes.map((code) => (
              <button
                key={code}
                onClick={() => toggle(code)}
                className={`sa-chip ${roles[code] ? "active" : ""}`}
                style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.4rem 0.6rem" }}
              >
                {roles[code] ? "🟢" : "🔴"} {ROLE_EMOJI[code] ?? "❓"} {code}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// === Timings editor ===

const TIMING_KEYS: { key: string; delta: number }[] = [
  { key: "registration", delta: 30 },
  { key: "night", delta: 15 },
  { key: "day", delta: 15 },
  { key: "mafia_vote", delta: 5 },
  { key: "hanging_vote", delta: 5 },
  { key: "hanging_confirm", delta: 5 },
  { key: "last_words", delta: 5 },
  { key: "afsungar_carry", delta: 5 },
];

export function TimingsEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
  const timings = settings.timings || {};

  const adjust = (key: string, delta: number) => {
    const current = Number(timings[key] ?? 0);
    const next = Math.max(5, Math.min(900, current + delta));
    onSave("timings", { ...timings, [key]: next });
  };

  return (
    <div>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
        ({t("admin.settings.timings_unit")})
      </p>
      {TIMING_KEYS.map(({ key, delta }) => (
        <div
          key={key}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "0.5rem",
            padding: "0.4rem 0",
            borderBottom: "1px solid #2a2a45",
          }}
        >
          <span>{t(`admin.settings.timing_${key}`)}</span>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <button className="sa-chip" onClick={() => adjust(key, -delta)}>
              ➖ {delta}
            </button>
            <span style={{ minWidth: "60px", textAlign: "center", fontWeight: 600 }}>
              {timings[key] ?? "—"}s
            </span>
            <button className="sa-chip" onClick={() => adjust(key, delta)}>
              ➕ {delta}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// === Items editor ===

const ITEM_LABELS: Record<string, string> = {
  shield: "🛡 Shield",
  killer_shield: "⛑ Killer shield",
  vote_shield: "⚖️ Vote shield",
  rifle: "🔫 Rifle",
  mask: "🎭 Mask",
  fake_document: "📁 Fake document",
};

export function ItemsEditor({ settings, onSave }: EditorProps) {
  const items = settings.items_allowed || {};
  const toggle = (code: string) => {
    onSave("items_allowed", { ...items, [code]: !items[code] });
  };
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
        gap: "0.4rem",
      }}
    >
      {Object.entries(ITEM_LABELS).map(([code, label]) => (
        <button
          key={code}
          onClick={() => toggle(code)}
          className={`sa-chip ${items[code] ? "active" : ""}`}
          style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.5rem 0.7rem" }}
        >
          {items[code] ? "🟢" : "🔴"} {label}
        </button>
      ))}
    </div>
  );
}

// === Silence editor ===

const SILENCE_KEYS = ["dead_players", "sleeping_players", "non_players", "night_chat"];

export function SilenceEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
  const silence = settings.silence || {};
  const toggle = (key: string) => {
    onSave("silence", { ...silence, [key]: !silence[key] });
  };

  const labelKey: Record<string, string> = {
    dead_players: "admin.settings.silence_dead",
    sleeping_players: "admin.settings.silence_sleeping",
    non_players: "admin.settings.silence_non_players",
    night_chat: "admin.settings.silence_night_chat",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {SILENCE_KEYS.map((key) => (
        <button
          key={key}
          onClick={() => toggle(key)}
          className={`sa-chip ${silence[key] ? "active" : ""}`}
          style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.6rem 0.8rem" }}
        >
          {silence[key] ? "🟢" : "🔴"} {t(labelKey[key])}
        </button>
      ))}
    </div>
  );
}

// === Gameplay editor ===

export function GameplayEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
  const g = (settings.gameplay as Record<string, unknown>) || {};
  const ratio = (g.mafia_ratio as string) ?? "low";

  const setRatio = (val: "low" | "high") => {
    onSave("gameplay", { ...g, mafia_ratio: val });
  };
  const toggleKey = (key: string) => {
    onSave("gameplay", { ...g, [key]: !g[key] });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <div>
        <p style={{ color: "var(--muted)", margin: "0.5rem 0", fontSize: "0.85rem" }}>
          {t("admin.settings.ratio")}
        </p>
        <div style={{ display: "flex", gap: "0.4rem" }}>
          <button
            className={`sa-chip ${ratio === "low" ? "active" : ""}`}
            onClick={() => setRatio("low")}
            style={{ flex: 1 }}
          >
            {t("admin.settings.ratio_low")}
          </button>
          <button
            className={`sa-chip ${ratio === "high" ? "active" : ""}`}
            onClick={() => setRatio("high")}
            style={{ flex: 1 }}
          >
            {t("admin.settings.ratio_high")}
          </button>
        </div>
      </div>

      <button
        onClick={() => toggleKey("allow_skip_day_vote")}
        className={`sa-chip ${g.allow_skip_day_vote ? "active" : ""}`}
        style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.6rem 0.8rem" }}
      >
        {g.allow_skip_day_vote ? "🟢" : "🔴"} {t("admin.settings.skip_day_vote")}
      </button>

      <button
        onClick={() => toggleKey("allow_skip_night_action")}
        className={`sa-chip ${g.allow_skip_night_action ? "active" : ""}`}
        style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.6rem 0.8rem" }}
      >
        {g.allow_skip_night_action ? "🟢" : "🔴"} {t("admin.settings.skip_night_action")}
      </button>
    </div>
  );
}

// === Language editor ===

export function LanguageEditor({ settings, onSave }: EditorProps) {
  const current = settings.language;
  const options: { code: string; label: string }[] = [
    { code: "uz", label: "🇺🇿 O'zbekcha" },
    { code: "ru", label: "🇷🇺 Русский" },
    { code: "en", label: "🇬🇧 English" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
      {options.map((o) => (
        <button
          key={o.code}
          onClick={() => onSave("language", o.code)}
          className={`sa-chip ${o.code === current ? "active" : ""}`}
          style={{ justifyContent: "flex-start", padding: "0.6rem 0.8rem" }}
        >
          {o.code === current ? "🟢" : "⚪"} {o.label}
        </button>
      ))}
    </div>
  );
}
