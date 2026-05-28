import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import WebApp from "@twa-dev/sdk";
import { useTranslation } from "react-i18next";
import { api } from "@shared/api/client";

import { ErrorBanner, Skeleton } from "../components/Ui";
import { LangPicker } from "@shared/components/LangPicker";
import { groupApi, type MessageTemplate } from "@shared/api/group";

// Static role emojis + i18n key suffix — name resolves at render time
// against the backend `role-*` keys (shared with the bot) so this list
// stays in sync with whatever the locale calls each role.
const ROLE_CODES = [
  "citizen", "detective", "sergeant", "mayor", "doctor",
  "hooker", "hobo", "lucky", "suicide", "kamikaze",
  "don", "mafia", "lawyer", "journalist", "killer",
  "maniac", "werewolf", "mage", "arsonist", "crook", "snitch",
] as const;
const ROLE_EMOJI: Record<string, string> = {
  citizen: "👨🏼", detective: "🕵🏻‍♂", sergeant: "👮🏻‍♂", mayor: "🎖",
  doctor: "👨🏻‍⚕", hooker: "💃", hobo: "🧙‍♂", lucky: "🤞🏼", suicide: "🤦🏼",
  kamikaze: "💣", don: "🤵🏻", mafia: "🤵🏼", lawyer: "👨‍💼", journalist: "👩🏼‍💻",
  killer: "🥷", maniac: "🔪", werewolf: "🐺", mage: "🧙", arsonist: "🧟",
  crook: "🤹", snitch: "🤓",
};

const TIMING_CODES = [
  "registration", "night", "day", "mafia_vote",
  "hanging_vote", "hanging_confirm", "last_words", "afsungar_carry",
] as const;
const SILENCE_CODES = [
  "dead_players", "sleeping_players", "non_players", "night_chat",
] as const;
const ITEM_CODES = [
  "shield", "killer_shield", "vote_shield", "rifle", "mask", "fake_document",
] as const;
const PERMISSION_CODES = [
  "who_can_register", "who_can_start", "who_can_extend", "who_can_stop",
] as const;
const AFK_CODES = [
  "skip_phases_before_kick",
  "xp_penalty_on_kick",
  "elo_penalty_on_leave",
  "consecutive_leaves_to_ban",
  "ban_duration_hours",
] as const;
// Language options for the LangPicker — label is rendered next to an SVG
// flag so this list intentionally carries no emoji prefix.
const LANG_OPTIONS = [
  { code: "uz", label: "O'zbekcha" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];
// Atmosphere events — same key set the bot's /setatmosphere command writes.
const ATMOSPHERE_EVENTS = [
  "night_start", "day_start", "voting_start",
  "game_end_civilian_win", "game_end_mafia_win", "game_end_singleton_win",
] as const;

interface GroupSettings {
  group_id: number;
  title: string;
  language: string;
  roles: Record<string, boolean>;
  timings: Record<string, number>;
  silence: Record<string, boolean>;
  items_allowed: Record<string, boolean>;
  role_distribution: Record<string, string[]>;
  permissions: Record<string, string | boolean>;
  gameplay: Record<string, string | number | boolean>;
  display: Record<string, boolean>;
  afk: Record<string, number>;
  atmosphere_media: Record<string, string>;
}

type Tab =
  | "roles"
  | "distribution"
  | "timings"
  | "items"
  | "silence"
  | "permissions"
  | "gameplay"
  | "display"
  | "afk"
  | "language"
  | "atmosphere"
  | "messages";

const PLAYER_COUNTS = Array.from({ length: 27 }, (_, i) => i + 4); // 4..30

// localStorage helper — keeps unsaved settings around across refresh /
// accidental nav-aways. Keyed by group so different chats don't collide.
const draftKey = (gid: number) => `mafia.webapp.draft.${gid}`;

function readDraft(gid: number): GroupSettings | null {
  try {
    const raw = localStorage.getItem(draftKey(gid));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeDraft(gid: number, draft: GroupSettings | null): void {
  try {
    if (draft === null) localStorage.removeItem(draftKey(gid));
    else localStorage.setItem(draftKey(gid), JSON.stringify(draft));
  } catch {
    // Quota or private-mode — failing silently is fine, draft is a
    // convenience not a correctness feature.
  }
}

export function GroupSettingsPage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("roles");
  const [draft, setDraft] = useState<GroupSettings | null>(null);
  const [dirty, setDirty] = useState(false);
  const [distN, setDistN] = useState<number>(8);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [draftRestoredNotice, setDraftRestoredNotice] = useState(false);

  const roleLabel = (code: string) => `${ROLE_EMOJI[code] ?? ""} ${t(`role-${code}`)}`.trim();
  const timingLabel = (code: string) => t(`group_settings.timing_${code}`);
  const silenceLabel = (code: string) => t(`group_settings.silence_${code}`);
  const permissionLabel = (code: string) => t(`group_settings.perm_${code}`);
  const itemLabel = (code: string) => t(`sa.system.item_${code}`);
  const afkLabel = (code: string) => t(`group_settings.afk_${code}`);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["settings", gid],
    queryFn: async () =>
      (await api.get<GroupSettings>(`/group/${gid}/settings`)).data,
    enabled: !!gid,
  });

  // Seed draft once data lands. Prefer localStorage if user had unsaved
  // edits — that's the whole point of persisting them.
  useEffect(() => {
    if (data && !draft) {
      const persisted = readDraft(gid);
      if (persisted && persisted.group_id === data.group_id) {
        setDraft(persisted);
        setDirty(true);
        setDraftRestoredNotice(true);
      } else {
        setDraft(data);
      }
    }
  }, [data, draft, gid]);

  const saveMutation = useMutation({
    mutationFn: async ({
      section,
      value,
    }: {
      section: string;
      value: unknown;
    }) => api.post(`/group/${gid}/settings`, { section, value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", gid] });
      try {
        WebApp.HapticFeedback?.notificationOccurred?.("success");
      } catch {
        // Outside Telegram — no haptics available.
      }
      setDirty(false);
      setSaveError(null);
      writeDraft(gid, null);
      setDraftRestoredNotice(false);
    },
    onError: () => {
      setSaveError(t("webapp.ux.error_save_failed"));
      try {
        WebApp.HapticFeedback?.notificationOccurred?.("error");
      } catch {
        // Outside Telegram.
      }
    },
  });

  if (isError) {
    return (
      <main>
        <ErrorBanner onRetry={() => refetch()} />
      </main>
    );
  }
  if (isLoading || !draft) {
    return (
      <main>
        <Skeleton rows={2} height={36} />
        <Skeleton rows={5} height={56} />
      </main>
    );
  }

  const updateField = (section: keyof GroupSettings, key: string, value: unknown) => {
    const next = {
      ...draft,
      [section]: { ...(draft[section] as Record<string, unknown>), [key]: value },
    };
    setDraft(next);
    setDirty(true);
    writeDraft(gid, next);
  };

  const discardDraft = () => {
    if (data) {
      setDraft(data);
      setDirty(false);
      writeDraft(gid, null);
      setDraftRestoredNotice(false);
    }
  };

  const saveCurrentTab = () => {
    setSaveError(null);
    if (tab === "roles") saveMutation.mutate({ section: "roles", value: draft.roles });
    else if (tab === "distribution")
      saveMutation.mutate({ section: "role_distribution", value: draft.role_distribution });
    else if (tab === "timings")
      saveMutation.mutate({ section: "timings", value: draft.timings });
    else if (tab === "items")
      saveMutation.mutate({ section: "items_allowed", value: draft.items_allowed });
    else if (tab === "silence")
      saveMutation.mutate({ section: "silence", value: draft.silence });
    else if (tab === "permissions")
      saveMutation.mutate({ section: "permissions", value: draft.permissions });
    else if (tab === "gameplay")
      saveMutation.mutate({ section: "gameplay", value: draft.gameplay });
    else if (tab === "display")
      saveMutation.mutate({ section: "display", value: draft.display });
    else if (tab === "afk") saveMutation.mutate({ section: "afk", value: draft.afk });
    else if (tab === "language")
      saveMutation.mutate({ section: "language", value: draft.language });
    // "atmosphere" and "messages" tabs have their own save flows.
  };

  const currentOverride: string[] | null =
    draft.role_distribution?.[String(distN)] ?? null;

  const setOverride = (newList: string[] | null) => {
    const next = { ...(draft.role_distribution ?? {}) };
    if (newList === null) {
      delete next[String(distN)];
    } else {
      next[String(distN)] = newList;
    }
    setDraft({ ...draft, role_distribution: next });
    setDirty(true);
    writeDraft(gid, { ...draft, role_distribution: next });
  };

  const enableOverride = () => {
    const seed: string[] = ["don", "detective"];
    while (seed.length < distN) seed.push("citizen");
    setOverride(seed);
  };

  const updateSlot = (index: number, newRole: string) => {
    if (currentOverride === null) return;
    const copy = [...currentOverride];
    copy[index] = newRole;
    setOverride(copy);
  };

  // Tabs that have their own save flow shouldn't show the global save bar.
  const showSaveBar = tab !== "atmosphere" && tab !== "messages";

  return (
    <main className={showSaveBar ? "with-sticky-save" : ""}>
      <h2 style={{ marginBottom: "0.5rem" }}>⚙️ {draft.title}</h2>
      <p style={{ color: "var(--muted)", marginTop: 0, fontSize: "0.85rem" }}>
        {t("group_settings.group_id")}: {draft.group_id}
      </p>

      {draftRestoredNotice && (
        <div className="webapp-notice">
          <span>{t("webapp.ux.draft_restored")}</span>
          <button className="webapp-btn webapp-btn-ghost" onClick={discardDraft}>
            {t("webapp.ux.draft_discard")}
          </button>
        </div>
      )}

      <div className="webapp-tabs">
        <TabBtn id="roles" current={tab} setTab={setTab}>{t("group_settings.tab_roles")}</TabBtn>
        <TabBtn id="distribution" current={tab} setTab={setTab}>{t("group_settings.tab_distribution")}</TabBtn>
        <TabBtn id="timings" current={tab} setTab={setTab}>{t("group_settings.tab_timings")}</TabBtn>
        <TabBtn id="items" current={tab} setTab={setTab}>{t("group_settings.tab_items")}</TabBtn>
        <TabBtn id="silence" current={tab} setTab={setTab}>{t("group_settings.tab_silence")}</TabBtn>
        <TabBtn id="permissions" current={tab} setTab={setTab}>{t("group_settings.tab_permissions")}</TabBtn>
        <TabBtn id="gameplay" current={tab} setTab={setTab}>{t("group_settings.tab_gameplay")}</TabBtn>
        <TabBtn id="display" current={tab} setTab={setTab}>{t("group_settings.tab_display")}</TabBtn>
        <TabBtn id="afk" current={tab} setTab={setTab}>{t("group_settings.tab_afk")}</TabBtn>
        <TabBtn id="language" current={tab} setTab={setTab}>{t("group_settings.tab_language")}</TabBtn>
        <TabBtn id="atmosphere" current={tab} setTab={setTab}>{t("group_settings.tab_atmosphere")}</TabBtn>
        <TabBtn id="messages" current={tab} setTab={setTab}>{t("group_settings.tab_messages")}</TabBtn>
      </div>

      {tab === "roles" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_roles")}</h3>
          {ROLE_CODES.map((code) => (
            <Toggle
              key={code}
              label={roleLabel(code)}
              checked={!!draft.roles[code]}
              onChange={(v) => updateField("roles", code, v)}
            />
          ))}
        </div>
      )}

      {tab === "distribution" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_distribution")}</h3>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
            {t("group_settings.distribution_hint")}
          </p>

          <div className="webapp-row">
            <label>{t("group_settings.distribution_player_count")}</label>
            <select
              className="webapp-input"
              style={{ width: "auto" }}
              value={distN}
              onChange={(e) => setDistN(parseInt(e.target.value))}
            >
              {PLAYER_COUNTS.map((n) => (
                <option key={n} value={n}>
                  {n}{draft.role_distribution?.[String(n)] ? " ✓" : ""}
                </option>
              ))}
            </select>
          </div>

          {currentOverride === null ? (
            <div style={{ padding: "1rem 0" }}>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                {t("group_settings.distribution_using_algorithm", { n: distN })}
              </p>
              <button className="webapp-btn" onClick={enableOverride}>
                {t("group_settings.distribution_enable_override")}
              </button>
            </div>
          ) : (
            <>
              <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                {t("group_settings.distribution_slots_hint", { n: distN })}
              </p>
              {currentOverride.map((roleCode, idx) => (
                <div key={idx} className="webapp-row">
                  <label>#{idx + 1}</label>
                  <select
                    className="webapp-input"
                    style={{ width: "auto" }}
                    value={roleCode}
                    onChange={(e) => updateSlot(idx, e.target.value)}
                  >
                    {ROLE_CODES.map((code) => (
                      <option key={code} value={code}>
                        {ROLE_EMOJI[code]} {t(`role-${code}`)}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
              <button
                className="webapp-btn"
                style={{ marginTop: "0.5rem", background: "var(--danger, #c0392b)" }}
                onClick={() => setOverride(null)}
              >
                {t("group_settings.distribution_reset")}
              </button>
            </>
          )}
        </div>
      )}

      {tab === "timings" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_timings")}</h3>
          {TIMING_CODES.map((key) => (
            <NumInput
              key={key}
              label={timingLabel(key)}
              value={draft.timings[key] || 0}
              onChange={(v) => updateField("timings", key, v)}
            />
          ))}
        </div>
      )}

      {tab === "items" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_items")}</h3>
          {ITEM_CODES.map((code) => (
            <Toggle
              key={code}
              label={itemLabel(code)}
              checked={!!draft.items_allowed[code]}
              onChange={(v) => updateField("items_allowed", code, v)}
            />
          ))}
        </div>
      )}

      {tab === "silence" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_silence")}</h3>
          {SILENCE_CODES.map((key) => (
            <Toggle
              key={key}
              label={silenceLabel(key)}
              checked={!!draft.silence[key]}
              onChange={(v) => updateField("silence", key, v)}
            />
          ))}
        </div>
      )}

      {tab === "permissions" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_permissions")}</h3>
          {PERMISSION_CODES.map((key) => (
            <SelectField
              key={key}
              label={permissionLabel(key)}
              value={String(draft.permissions[key] ?? "all")}
              options={["all", "admins", "registrar", "none"]}
              optionLabels={{
                all: t("group_settings.perm_value_all"),
                admins: t("group_settings.perm_value_admins"),
                registrar: t("group_settings.perm_value_registrar"),
                none: t("group_settings.perm_value_none"),
              }}
              onChange={(v) => updateField("permissions", key, v)}
            />
          ))}
          <Toggle
            label={t("group_settings.allow_leave")}
            checked={!!draft.permissions.allow_leave}
            onChange={(v) => updateField("permissions", "allow_leave", v)}
          />
        </div>
      )}

      {tab === "gameplay" && (
        <div className="webapp-section">
          <h3>{t("group_settings.tab_gameplay")}</h3>
          <SelectField
            label={t("group_settings.mafia_ratio")}
            value={String(draft.gameplay.mafia_ratio || "low")}
            options={["low", "high"]}
            optionLabels={{
              low: t("group_settings.mafia_ratio_low"),
              high: t("group_settings.mafia_ratio_high"),
            }}
            onChange={(v) => updateField("gameplay", "mafia_ratio", v)}
          />
          <NumInput
            label={t("group_settings.min_players")}
            value={Number(draft.gameplay.min_players || 4)}
            onChange={(v) => updateField("gameplay", "min_players", v)}
          />
          <NumInput
            label={t("group_settings.max_players")}
            value={Number(draft.gameplay.max_players || 30)}
            onChange={(v) => updateField("gameplay", "max_players", v)}
          />
          <Toggle
            label={t("group_settings.skip_day_vote")}
            checked={!!draft.gameplay.allow_skip_day_vote}
            onChange={(v) => updateField("gameplay", "allow_skip_day_vote", v)}
          />
          <Toggle
            label={t("group_settings.skip_night_action")}
            checked={!!draft.gameplay.allow_skip_night_action}
            onChange={(v) => updateField("gameplay", "allow_skip_night_action", v)}
          />
        </div>
      )}

      {tab === "display" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_display")}</h3>
          <Toggle
            label={t("group_settings.show_role_emojis")}
            checked={!!draft.display.show_role_emojis}
            onChange={(v) => updateField("display", "show_role_emojis", v)}
          />
          <Toggle
            label={t("group_settings.group_roles_in_list")}
            checked={!!draft.display.group_roles_in_list}
            onChange={(v) => updateField("display", "group_roles_in_list", v)}
          />
          <Toggle
            label={t("group_settings.anonymous_voting")}
            checked={!!draft.display.anonymous_voting}
            onChange={(v) => updateField("display", "anonymous_voting", v)}
          />
          <Toggle
            label={t("group_settings.auto_pin_registration")}
            checked={!!draft.display.auto_pin_registration}
            onChange={(v) => updateField("display", "auto_pin_registration", v)}
          />
          <Toggle
            label={t("group_settings.show_role_on_death")}
            checked={!!draft.display.show_role_on_death}
            onChange={(v) => updateField("display", "show_role_on_death", v)}
          />
        </div>
      )}

      {tab === "afk" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_afk")}</h3>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
            {t("group_settings.afk_hint")}
          </p>
          {AFK_CODES.map((key) => (
            <NumInput
              key={key}
              label={afkLabel(key)}
              value={draft.afk?.[key] ?? 0}
              onChange={(v) => updateField("afk", key, v)}
            />
          ))}
        </div>
      )}

      {tab === "language" && (
        <div className="webapp-section">
          <h3>{t("group_settings.section_language")}</h3>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
            {t("group_settings.language_hint")}
          </p>
          <div className="webapp-row">
            <label>{t("group_settings.language_label")}</label>
            <LangPicker
              value={draft.language}
              options={LANG_OPTIONS}
              onChange={(code) => {
                const next = { ...draft, language: code };
                setDraft(next);
                setDirty(true);
                writeDraft(gid, next);
              }}
            />
          </div>
        </div>
      )}

      {tab === "atmosphere" && (
        <AtmosphereTab
          groupId={gid}
          media={draft.atmosphere_media || {}}
          onClearedLocal={(event) => {
            const next = { ...(draft.atmosphere_media || {}) };
            delete next[event];
            setDraft({ ...draft, atmosphere_media: next });
            // No global-bar save needed — clearAtmosphere is its own POST.
          }}
        />
      )}

      {tab === "messages" && <MessagesTab groupId={gid} />}

      {saveError && (
        <div className="webapp-error-banner" style={{ margin: "0.75rem 0" }}>
          {saveError}
        </div>
      )}

      {showSaveBar && (
        <button
          className="webapp-save-btn"
          onClick={saveCurrentTab}
          disabled={!dirty || saveMutation.isPending}
        >
          {saveMutation.isPending
            ? t("group_settings.save_saving")
            : dirty
              ? t("group_settings.save_dirty")
              : t("group_settings.save_saved")}
        </button>
      )}
    </main>
  );
}

// === Tab body components ===

function AtmosphereTab({
  groupId,
  media,
  onClearedLocal,
}: {
  groupId: number;
  media: Record<string, string>;
  onClearedLocal: (event: string) => void;
}) {
  const { t } = useTranslation();
  const [busyEvent, setBusyEvent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const clear = async (event: string) => {
    setBusyEvent(event);
    setError(null);
    try {
      await groupApi.clearAtmosphere(groupId, event);
      onClearedLocal(event);
      try {
        WebApp.HapticFeedback?.notificationOccurred?.("success");
      } catch {
        // Outside Telegram.
      }
    } catch {
      setError(t("webapp.ux.error_save_failed"));
    } finally {
      setBusyEvent(null);
    }
  };

  return (
    <div className="webapp-section">
      <h3>{t("group_settings.section_atmosphere")}</h3>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
        {t("group_settings.atmosphere_hint")}
      </p>
      {error && <ErrorBanner message={error} />}
      {ATMOSPHERE_EVENTS.map((event) => {
        const fileId = media[event];
        return (
          <div key={event} className="webapp-row webapp-atmosphere-row">
            <label>{t(`group_settings.atmosphere_event_${event}`)}</label>
            <span className="webapp-atmosphere-status">
              {fileId ? (
                <code title={fileId}>{fileId.slice(0, 14)}…</code>
              ) : (
                <span style={{ color: "var(--muted)" }}>
                  {t("group_settings.atmosphere_no_media")}
                </span>
              )}
            </span>
            {fileId && (
              <button
                className="webapp-btn webapp-btn-ghost"
                disabled={busyEvent === event}
                onClick={() => clear(event)}
              >
                {t("group_settings.atmosphere_clear")}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

function MessagesTab({ groupId }: { groupId: number }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["messages", groupId],
    queryFn: () => groupApi.listMessages(groupId),
    enabled: !!groupId,
  });

  // Local override state so the user can edit several at once before saving.
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      const next: Record<string, string> = {};
      for (const tpl of data.items) {
        next[tpl.key] = tpl.override;
      }
      setOverrides(next);
      setDirty(false);
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () => groupApi.saveMessages(groupId, overrides),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", groupId] });
      setDirty(false);
      setError(null);
      try {
        WebApp.HapticFeedback?.notificationOccurred?.("success");
      } catch {
        // Outside Telegram.
      }
    },
    onError: () => setError(t("webapp.ux.error_save_failed")),
  });

  if (isError) {
    return (
      <div className="webapp-section">
        <ErrorBanner onRetry={() => refetch()} />
      </div>
    );
  }
  if (isLoading || !data) {
    return (
      <div className="webapp-section">
        <Skeleton rows={3} height={120} />
      </div>
    );
  }

  return (
    <div className="webapp-section">
      <h3>{t("group_settings.section_messages")}</h3>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
        {t("group_settings.messages_hint")}
      </p>
      {error && <ErrorBanner message={error} />}
      {data.items.map((tpl: MessageTemplate) => (
        <div key={tpl.key} className="webapp-message-editor">
          <h4>{t(`group_settings.messages_key_${tpl.key}`)}</h4>
          <div className="webapp-message-default">
            <small>{t("group_settings.messages_default_label")}</small>
            <pre>{tpl.default || "—"}</pre>
          </div>
          <label>
            <small>{t("group_settings.messages_override_label")}</small>
            <textarea
              className="webapp-input webapp-textarea"
              value={overrides[tpl.key] ?? ""}
              rows={3}
              onChange={(e) => {
                setOverrides({ ...overrides, [tpl.key]: e.target.value });
                setDirty(true);
              }}
            />
          </label>
          <small style={{ color: "var(--muted)" }}>
            {t("group_settings.messages_placeholders_label")}: <code>{tpl.placeholders}</code>
          </small>
        </div>
      ))}
      <button
        className="webapp-save-btn"
        onClick={() => saveMutation.mutate()}
        disabled={!dirty || saveMutation.isPending}
        style={{ marginTop: "1rem" }}
      >
        {saveMutation.isPending
          ? t("group_settings.save_saving")
          : dirty
            ? t("group_settings.save_dirty")
            : t("group_settings.save_saved")}
      </button>
    </div>
  );
}

// === Primitives ===

function TabBtn({
  id,
  current,
  setTab,
  children,
}: {
  id: Tab;
  current: Tab;
  setTab: (t: Tab) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      className={`webapp-tab ${current === id ? "active" : ""}`}
      onClick={() => setTab(id)}
    >
      {children}
    </button>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="webapp-row">
      <label>{label}</label>
      <span className="toggle">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="toggle-slider" />
      </span>
    </div>
  );
}

function NumInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="webapp-row">
      <label>{label}</label>
      <input
        type="number"
        className="webapp-input"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value) || 0)}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  options,
  optionLabels,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  optionLabels?: Record<string, string>;
  onChange: (v: string) => void;
}) {
  return (
    <div className="webapp-row">
      <label>{label}</label>
      <select
        className="webapp-input"
        style={{ width: "auto" }}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {optionLabels?.[o] ?? o}
          </option>
        ))}
      </select>
    </div>
  );
}
