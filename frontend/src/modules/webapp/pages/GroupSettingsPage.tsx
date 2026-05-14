import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import WebApp from "@twa-dev/sdk";
import { useTranslation } from "react-i18next";
import { api } from "@shared/api/client";

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

interface GroupSettings {
  group_id: number;
  title: string;
  language: string;
  roles: Record<string, boolean>;
  timings: Record<string, number>;
  silence: Record<string, boolean>;
  items_allowed: Record<string, boolean>;
  permissions: Record<string, string | boolean>;
  gameplay: Record<string, string | number | boolean>;
  display: Record<string, boolean>;
}

type Tab = "roles" | "timings" | "items" | "silence" | "permissions" | "gameplay" | "display";

export function GroupSettingsPage() {
  const { t } = useTranslation();
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("roles");
  const [draft, setDraft] = useState<GroupSettings | null>(null);
  const [dirty, setDirty] = useState(false);

  const roleLabel = (code: string) => `${ROLE_EMOJI[code] ?? ""} ${t(`role-${code}`)}`.trim();
  const timingLabel = (code: string) => t(`group_settings.timing_${code}`);
  const silenceLabel = (code: string) => t(`group_settings.silence_${code}`);
  const permissionLabel = (code: string) => t(`group_settings.perm_${code}`);
  const itemLabel = (code: string) => t(`sa.system.item_${code}`);

  const { data, isLoading } = useQuery({
    queryKey: ["settings", gid],
    queryFn: async () =>
      (await api.get<GroupSettings>(`/group/${gid}/settings`)).data,
    enabled: !!gid,
  });

  // Initialize draft when data loads
  if (data && !draft) {
    setDraft(data);
  }

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
      } catch {}
      setDirty(false);
    },
  });

  if (isLoading || !draft) return <div className="webapp-loading">⏳</div>;

  const updateField = (section: keyof GroupSettings, key: string, value: unknown) => {
    setDraft({
      ...draft,
      [section]: { ...(draft[section] as Record<string, unknown>), [key]: value },
    });
    setDirty(true);
  };

  const saveCurrentTab = () => {
    if (tab === "roles") saveMutation.mutate({ section: "roles", value: draft.roles });
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
  };

  return (
    <main>
      <h2 style={{ marginBottom: "0.5rem" }}>⚙️ {draft.title}</h2>
      <p style={{ color: "var(--muted)", marginTop: 0, fontSize: "0.85rem" }}>
        {t("group_settings.group_id")}: {draft.group_id}
      </p>

      <div className="webapp-tabs">
        <Tab id="roles" current={tab} setTab={setTab}>{t("group_settings.tab_roles")}</Tab>
        <Tab id="timings" current={tab} setTab={setTab}>{t("group_settings.tab_timings")}</Tab>
        <Tab id="items" current={tab} setTab={setTab}>{t("group_settings.tab_items")}</Tab>
        <Tab id="silence" current={tab} setTab={setTab}>{t("group_settings.tab_silence")}</Tab>
        <Tab id="permissions" current={tab} setTab={setTab}>{t("group_settings.tab_permissions")}</Tab>
        <Tab id="gameplay" current={tab} setTab={setTab}>{t("group_settings.tab_gameplay")}</Tab>
        <Tab id="display" current={tab} setTab={setTab}>{t("group_settings.tab_display")}</Tab>
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
    </main>
  );
}

function Tab({
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
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
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
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}
