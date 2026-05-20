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
            {t(`sa.settings.team_${group.team}`)}
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
                {roles[code] ? "🟢" : "🔴"} {ROLE_EMOJI[code] ?? "❓"} {t(`role-${code}`)}
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
        ({t("sa.settings.timings_unit")})
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
            flexWrap: "wrap",
          }}
        >
          <span style={{ flex: "1 1 50%", minWidth: 0, wordBreak: "break-word" }}>
            {t(`sa.settings.timing_${key}`)}
          </span>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.3rem",
              flex: "0 0 auto",
            }}
          >
            <button
              className="sa-chip"
              onClick={() => adjust(key, -delta)}
              style={{ padding: "0.3rem 0.5rem" }}
            >
              ➖ {delta}
            </button>
            <span style={{ minWidth: "48px", textAlign: "center", fontWeight: 600 }}>
              {timings[key] ?? "—"}s
            </span>
            <button
              className="sa-chip"
              onClick={() => adjust(key, delta)}
              style={{ padding: "0.3rem 0.5rem" }}
            >
              ➕ {delta}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// === Items editor ===

const ITEM_CODES = [
  "shield",
  "killer_shield",
  "vote_shield",
  "rifle",
  "mask",
  "fake_document",
] as const;

export function ItemsEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
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
      {ITEM_CODES.map((code) => (
        <button
          key={code}
          onClick={() => toggle(code)}
          className={`sa-chip ${items[code] ? "active" : ""}`}
          style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.5rem 0.7rem" }}
        >
          {items[code] ? "🟢" : "🔴"} {t(`sa.system.item_${code}`)}
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
    dead_players: "sa.settings.silence_dead",
    sleeping_players: "sa.settings.silence_sleeping",
    non_players: "sa.settings.silence_non_players",
    night_chat: "sa.settings.silence_night_chat",
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
          {t("sa.settings.ratio")}
        </p>
        <div style={{ display: "flex", gap: "0.4rem" }}>
          <button
            className={`sa-chip ${ratio === "low" ? "active" : ""}`}
            onClick={() => setRatio("low")}
            style={{ flex: 1 }}
          >
            {t("sa.settings.ratio_low")}
          </button>
          <button
            className={`sa-chip ${ratio === "high" ? "active" : ""}`}
            onClick={() => setRatio("high")}
            style={{ flex: 1 }}
          >
            {t("sa.settings.ratio_high")}
          </button>
        </div>
      </div>

      <button
        onClick={() => toggleKey("allow_skip_day_vote")}
        className={`sa-chip ${g.allow_skip_day_vote ? "active" : ""}`}
        style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.6rem 0.8rem" }}
      >
        {g.allow_skip_day_vote ? "🟢" : "🔴"} {t("sa.settings.skip_day_vote")}
      </button>

      <button
        onClick={() => toggleKey("allow_skip_night_action")}
        className={`sa-chip ${g.allow_skip_night_action ? "active" : ""}`}
        style={{ justifyContent: "flex-start", textAlign: "left", padding: "0.6rem 0.8rem" }}
      >
        {g.allow_skip_night_action ? "🟢" : "🔴"} {t("sa.settings.skip_night_action")}
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


// === Per-group role-emoji overrides ===========================
// Writes/reads to `display.role_emojis` (a dict keyed by role slug).
// Value shape: { custom_id: string, fallback: string }.
// Empty fields are removed on save so we never persist no-op entries.

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { saApi, type RoleConfig } from "@shared/api/sa";

type Override = { custom_id: string; fallback: string };

export function RoleEmojiOverridesEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
  const { data: configs } = useQuery({
    queryKey: ["sa-role-configs"],
    queryFn: saApi.roleConfigs,
    staleTime: 60_000,
  });

  const stored: Record<string, Override | unknown> =
    ((settings.display as Record<string, unknown>)?.role_emojis as Record<string, unknown>) || {};

  const [draft, setDraft] = useState<Record<string, Override>>(() =>
    Object.fromEntries(
      Object.entries(stored).map(([k, v]) => [k, normalize(v)]),
    ),
  );
  useEffect(() => {
    setDraft(
      Object.fromEntries(
        Object.entries(stored).map(([k, v]) => [k, normalize(v)]),
      ),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.group_id]);

  const updateDraft = (role: string, patch: Partial<Override>) => {
    setDraft((prev) => ({
      ...prev,
      [role]: { ...(prev[role] ?? { custom_id: "", fallback: "" }), ...patch },
    }));
  };

  const clear = (role: string) => {
    setDraft((prev) => {
      const { [role]: _drop, ...rest } = prev;
      return rest;
    });
  };

  const onCommit = () => {
    // Drop entries where both fields are blank
    const clean: Record<string, Override> = {};
    for (const [k, v] of Object.entries(draft)) {
      if (v.custom_id.trim() || v.fallback.trim()) {
        clean[k] = {
          custom_id: v.custom_id.trim(),
          fallback: v.fallback.trim(),
        };
      }
    }
    onSave("display", {
      ...((settings.display as Record<string, unknown>) || {}),
      role_emojis: clean,
    });
  };

  const items = (configs?.items ?? []).slice().sort((a, b) => a.order_idx - b.order_idx);

  if (items.length === 0)
    return <p style={{ color: "var(--muted)" }}>{t("loading")}…</p>;

  return (
    <>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>
        {t("sa.group_detail.role_emojis_hint")}
      </p>
      <div style={{ display: "grid", gap: 6 }}>
        {items.map((cfg) => (
          <RoleOverrideRow
            key={cfg.role}
            cfg={cfg}
            override={draft[cfg.role]}
            onChange={(patch) => updateDraft(cfg.role, patch)}
            onClear={() => clear(cfg.role)}
          />
        ))}
      </div>
      <button
        className="sa-chip active"
        onClick={onCommit}
        style={{ marginTop: 12, padding: "0.5rem 1rem" }}
      >
        💾 {t("save")}
      </button>
    </>
  );
}

function RoleOverrideRow({
  cfg, override, onChange, onClear,
}: {
  cfg: RoleConfig;
  override: Override | undefined;
  onChange: (patch: Partial<Override>) => void;
  onClear: () => void;
}) {
  const { t } = useTranslation();
  const customId = override?.custom_id ?? "";
  const fallback = override?.fallback ?? "";
  const effective = fallback || cfg.static_emoji;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "32px 1fr auto",
        gap: 6,
        alignItems: "center",
        padding: "6px 0",
        borderBottom: "1px solid #2a2a45",
      }}
    >
      <div style={{ fontSize: 22, textAlign: "center" }} title={cfg.role}>{effective}</div>
      <div style={{ display: "grid", gap: 4 }}>
        <div style={{ fontSize: 12 }}>
          <strong>{cfg.name_uz}</strong>
          <code style={{ marginLeft: 6, color: "var(--muted)", fontSize: 10 }}>{cfg.role}</code>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "44px 1fr", gap: 4 }}>
          <input
            className="sa-input"
            value={fallback}
            onChange={(e) => onChange({ fallback: e.target.value })}
            placeholder={cfg.static_emoji}
            style={{ width: 44, textAlign: "center", fontSize: 16, padding: "3px 4px" }}
          />
          <input
            className="sa-input"
            value={customId}
            onChange={(e) => onChange({ custom_id: e.target.value })}
            placeholder={cfg.custom_emoji_id || t("admin.role_configs.custom_id_placeholder")}
            style={{ fontFamily: "monospace", fontSize: 11, padding: "3px 6px" }}
          />
        </div>
      </div>
      {(customId || fallback) && (
        <button
          className="sa-chip"
          onClick={onClear}
          style={{ padding: "2px 8px", fontSize: 11 }}
          title="reset"
        >
          ✕
        </button>
      )}
    </div>
  );
}

function normalize(v: unknown): Override {
  if (Array.isArray(v) && v.length === 2) {
    return { custom_id: String(v[0] ?? ""), fallback: String(v[1] ?? "") };
  }
  if (v && typeof v === "object") {
    const o = v as Record<string, unknown>;
    return {
      custom_id: String(o.custom_id ?? ""),
      fallback: String(o.fallback ?? o.emoji ?? ""),
    };
  }
  return { custom_id: "", fallback: "" };
}


// === Per-group standalone-emoji overrides (scene / item / action / …) ====
// Writes/reads `display.custom_emojis`. Shape: `{ code: {custom_id, fallback} }`.
// Empty rows are dropped on save.

import type { EmojiConfig } from "@shared/api/sa";

export function CustomEmojiOverridesEditor({ settings, onSave }: EditorProps) {
  const { t } = useTranslation();
  const { data: configs } = useQuery({
    queryKey: ["sa-emoji-configs"],
    queryFn: saApi.emojiConfigs,
    staleTime: 60_000,
  });

  const stored = (((settings.display as Record<string, unknown>)?.custom_emojis as
    Record<string, unknown>) || {});
  const [draft, setDraft] = useState<Record<string, Override>>(() =>
    Object.fromEntries(Object.entries(stored).map(([k, v]) => [k, normalize(v)])),
  );
  useEffect(() => {
    setDraft(Object.fromEntries(Object.entries(stored).map(([k, v]) => [k, normalize(v)])));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.group_id]);

  const items = (configs?.items ?? []).slice().sort((a, b) => a.order_idx - b.order_idx);
  const grouped = useMemo(() => {
    const out: Record<string, EmojiConfig[]> = {};
    items.forEach((c) => {
      (out[c.category] ??= []).push(c);
    });
    return out;
  }, [items]);

  const updateDraft = (code: string, patch: Partial<Override>) =>
    setDraft((p) => ({
      ...p,
      [code]: { ...(p[code] ?? { custom_id: "", fallback: "" }), ...patch },
    }));
  const clear = (code: string) =>
    setDraft((p) => {
      const { [code]: _, ...rest } = p;
      return rest;
    });

  const onCommit = () => {
    const clean: Record<string, Override> = {};
    for (const [k, v] of Object.entries(draft)) {
      if (v.custom_id.trim() || v.fallback.trim()) {
        clean[k] = { custom_id: v.custom_id.trim(), fallback: v.fallback.trim() };
      }
    }
    onSave("display", {
      ...((settings.display as Record<string, unknown>) || {}),
      custom_emojis: clean,
    });
  };

  if (items.length === 0)
    return <p style={{ color: "var(--muted)" }}>{t("loading")}…</p>;

  const CAT_ORDER: string[] = ["scene", "status", "item", "action", "currency"];

  return (
    <>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 0.75rem" }}>
        {t("sa.group_detail.custom_emojis_hint")}
      </p>
      {CAT_ORDER.map((cat) =>
        grouped[cat] && grouped[cat].length > 0 ? (
          <details key={cat} style={{ marginBottom: 12 }}>
            <summary style={{ cursor: "pointer", color: "var(--accent)" }}>
              {t(`admin.emoji_configs.cat_${cat}`)}
              <span style={{ color: "var(--muted)" }}> ({grouped[cat].length})</span>
            </summary>
            <div style={{ display: "grid", gap: 6, marginTop: 6 }}>
              {grouped[cat].map((cfg) => (
                <EmojiOverrideRow
                  key={cfg.code}
                  cfg={cfg}
                  override={draft[cfg.code]}
                  onChange={(patch) => updateDraft(cfg.code, patch)}
                  onClear={() => clear(cfg.code)}
                />
              ))}
            </div>
          </details>
        ) : null,
      )}
      <button
        className="sa-chip active"
        onClick={onCommit}
        style={{ marginTop: 12, padding: "0.5rem 1rem" }}
      >
        💾 {t("save")}
      </button>
    </>
  );
}

function EmojiOverrideRow({
  cfg, override, onChange, onClear,
}: {
  cfg: EmojiConfig;
  override: Override | undefined;
  onChange: (patch: Partial<Override>) => void;
  onClear: () => void;
}) {
  const { t } = useTranslation();
  const customId = override?.custom_id ?? "";
  const fallback = override?.fallback ?? "";
  const effective = fallback || cfg.static_emoji;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "32px 1fr auto",
        gap: 6,
        alignItems: "center",
        padding: "5px 0",
        borderBottom: "1px solid #2a2a45",
      }}
    >
      <div style={{ fontSize: 20, textAlign: "center" }}>{effective}</div>
      <div style={{ display: "grid", gap: 4 }}>
        <div style={{ fontSize: 11 }}>
          <strong>{cfg.name_uz}</strong>
          <code style={{ marginLeft: 6, color: "var(--muted)", fontSize: 9 }}>{cfg.code}</code>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "40px 1fr", gap: 4 }}>
          <input className="sa-input" value={fallback} placeholder={cfg.static_emoji}
            onChange={(e) => onChange({ fallback: e.target.value })}
            style={{ width: 40, textAlign: "center", fontSize: 14, padding: "2px 3px" }} />
          <input className="sa-input" value={customId}
            placeholder={cfg.custom_emoji_id || t("admin.role_configs.custom_id_placeholder")}
            onChange={(e) => onChange({ custom_id: e.target.value })}
            style={{ fontFamily: "monospace", fontSize: 10, padding: "2px 5px" }} />
        </div>
      </div>
      {(customId || fallback) && (
        <button className="sa-chip" onClick={onClear}
          style={{ padding: "2px 6px", fontSize: 10 }} title="reset">
          ✕
        </button>
      )}
    </div>
  );
}
