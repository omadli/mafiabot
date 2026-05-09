import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import WebApp from "@twa-dev/sdk";
import { api } from "@shared/api/client";

const ROLE_LABELS: Record<string, string> = {
  citizen: "👨🏼 Tinch aholi",
  detective: "🕵🏻‍♂ Komissar",
  sergeant: "👮🏻‍♂ Serjant",
  mayor: "🎖 Janob",
  doctor: "👨🏻‍⚕ Doktor",
  hooker: "💃 Kezuvchi",
  hobo: "🧙‍♂ Daydi",
  lucky: "🤞🏼 Omadli",
  suicide: "🤦🏼 Suidsid",
  kamikaze: "💣 Afsungar",
  don: "🤵🏻 Don",
  mafia: "🤵🏼 Mafiya",
  lawyer: "👨‍💼 Advokat",
  journalist: "👩🏼‍💻 Jurnalist",
  killer: "🥷 Ninza",
  maniac: "🔪 Qotil",
  werewolf: "🐺 Bo'ri",
  mage: "🧙 Sehrgar",
  arsonist: "🧟 G'azabkor",
  crook: "🤹 Aferist",
  snitch: "🤓 Sotqin",
};

const TIMING_LABELS: Record<string, string> = {
  registration: "Ro'yxatdan o'tish",
  night: "Tun",
  day: "Kun",
  mafia_vote: "Mafia ovozi",
  hanging_vote: "Osishga ovoz",
  hanging_confirm: "Tasdiq (👍/👎)",
  last_words: "So'nggi so'z",
  afsungar_carry: "Afsungar olib ketish",
};

const SILENCE_LABELS: Record<string, string> = {
  dead_players: "O'lganlar yozolmaydi",
  sleeping_players: "Uxlaganlar yozolmaydi",
  non_players: "O'ynamayotganlar yozolmaydi",
  night_chat: "Tunda hech kim yozolmaydi",
};

const ITEM_LABELS: Record<string, string> = {
  shield: "🛡 Himoya",
  killer_shield: "⛑ Qotildan himoya",
  vote_shield: "⚖️ Ovoz himoyasi",
  rifle: "🔫 Miltiq",
  mask: "🎭 Maska",
  fake_document: "📁 Soxta hujjat",
};

const PERMISSION_LABELS: Record<string, string> = {
  who_can_register: "Ro'yxatdan o'tishni kim boshlay oladi",
  who_can_start: "O'yinni kim boshlay oladi",
  who_can_extend: "Vaqtni kim uzaytira oladi",
  who_can_stop: "Kim to'xtata oladi",
};

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
  const { groupId } = useParams();
  const gid = parseInt(groupId || "0");
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("roles");
  const [draft, setDraft] = useState<GroupSettings | null>(null);
  const [dirty, setDirty] = useState(false);

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
        Group ID: {draft.group_id}
      </p>

      <div className="webapp-tabs">
        <Tab id="roles" current={tab} setTab={setTab}>🎭 Rollar</Tab>
        <Tab id="timings" current={tab} setTab={setTab}>⏱ Vaqtlar</Tab>
        <Tab id="items" current={tab} setTab={setTab}>🛡 Itemlar</Tab>
        <Tab id="silence" current={tab} setTab={setTab}>🔇 Jimlik</Tab>
        <Tab id="permissions" current={tab} setTab={setTab}>🔐 Ruxsatlar</Tab>
        <Tab id="gameplay" current={tab} setTab={setTab}>🎮 Gameplay</Tab>
        <Tab id="display" current={tab} setTab={setTab}>👁 Ko'rinish</Tab>
      </div>

      {tab === "roles" && (
        <div className="webapp-section">
          <h3>Yoqilgan rollar</h3>
          {Object.keys(ROLE_LABELS).map((code) => (
            <Toggle
              key={code}
              label={ROLE_LABELS[code]}
              checked={!!draft.roles[code]}
              onChange={(v) => updateField("roles", code, v)}
            />
          ))}
        </div>
      )}

      {tab === "timings" && (
        <div className="webapp-section">
          <h3>Vaqt sozlamalari (sekund)</h3>
          {Object.keys(TIMING_LABELS).map((key) => (
            <NumInput
              key={key}
              label={TIMING_LABELS[key]}
              value={draft.timings[key] || 0}
              onChange={(v) => updateField("timings", key, v)}
            />
          ))}
        </div>
      )}

      {tab === "items" && (
        <div className="webapp-section">
          <h3>Guruhda yoqilgan itemlar</h3>
          {Object.keys(ITEM_LABELS).map((code) => (
            <Toggle
              key={code}
              label={ITEM_LABELS[code]}
              checked={!!draft.items_allowed[code]}
              onChange={(v) => updateField("items_allowed", code, v)}
            />
          ))}
        </div>
      )}

      {tab === "silence" && (
        <div className="webapp-section">
          <h3>Jimlik qoidalari</h3>
          {Object.keys(SILENCE_LABELS).map((key) => (
            <Toggle
              key={key}
              label={SILENCE_LABELS[key]}
              checked={!!draft.silence[key]}
              onChange={(v) => updateField("silence", key, v)}
            />
          ))}
        </div>
      )}

      {tab === "permissions" && (
        <div className="webapp-section">
          <h3>Buyruq ruxsatlari</h3>
          {Object.keys(PERMISSION_LABELS).map((key) => (
            <SelectField
              key={key}
              label={PERMISSION_LABELS[key]}
              value={String(draft.permissions[key] ?? "all")}
              options={["all", "admins", "registrar", "none"]}
              onChange={(v) => updateField("permissions", key, v)}
            />
          ))}
          <Toggle
            label="✋ /leave ruxsat"
            checked={!!draft.permissions.allow_leave}
            onChange={(v) => updateField("permissions", "allow_leave", v)}
          />
        </div>
      )}

      {tab === "gameplay" && (
        <div className="webapp-section">
          <h3>Gameplay</h3>
          <SelectField
            label="Mafia nisbati"
            value={String(draft.gameplay.mafia_ratio || "low")}
            options={["low", "high"]}
            onChange={(v) => updateField("gameplay", "mafia_ratio", v)}
          />
          <NumInput
            label="Min o'yinchi"
            value={Number(draft.gameplay.min_players || 4)}
            onChange={(v) => updateField("gameplay", "min_players", v)}
          />
          <NumInput
            label="Max o'yinchi"
            value={Number(draft.gameplay.max_players || 30)}
            onChange={(v) => updateField("gameplay", "max_players", v)}
          />
          <Toggle
            label="Kunduzi 'Hech kim' varianti"
            checked={!!draft.gameplay.allow_skip_day_vote}
            onChange={(v) => updateField("gameplay", "allow_skip_day_vote", v)}
          />
          <Toggle
            label="Tunda 'Skip' tugmasi"
            checked={!!draft.gameplay.allow_skip_night_action}
            onChange={(v) => updateField("gameplay", "allow_skip_night_action", v)}
          />
        </div>
      )}

      {tab === "display" && (
        <div className="webapp-section">
          <h3>Ko'rinish</h3>
          <Toggle
            label="Rollar emoji bilan"
            checked={!!draft.display.show_role_emojis}
            onChange={(v) => updateField("display", "show_role_emojis", v)}
          />
          <Toggle
            label="Rollarni guruhlab ko'rsatish"
            checked={!!draft.display.group_roles_in_list}
            onChange={(v) => updateField("display", "group_roles_in_list", v)}
          />
          <Toggle
            label="Anonim ovoz berish"
            checked={!!draft.display.anonymous_voting}
            onChange={(v) => updateField("display", "anonymous_voting", v)}
          />
          <Toggle
            label="Ro'yxatni avto-pin qilish"
            checked={!!draft.display.auto_pin_registration}
            onChange={(v) => updateField("display", "auto_pin_registration", v)}
          />
          <Toggle
            label="O'lganda rolini ko'rsatish"
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
        {saveMutation.isPending ? "💾 Saqlanmoqda..." : dirty ? "💾 Saqlash" : "✅ Saqlangan"}
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
