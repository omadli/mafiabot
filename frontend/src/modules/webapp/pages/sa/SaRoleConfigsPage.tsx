import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi, type RoleConfig, type RoleTeam } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

type EditableFields = Pick<
  RoleConfig,
  "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id"
>;

const TEAM_ORDER: RoleTeam[] = ["civilians", "mafia", "singletons"];

const TEAM_META: Record<RoleTeam, { emoji: string; key: string }> = {
  civilians:  { emoji: "👨‍👨‍👧‍👦", key: "admin.role_configs.team_civilians" },
  mafia:      { emoji: "🤵🏼",   key: "admin.role_configs.team_mafia" },
  singletons: { emoji: "🎯",    key: "admin.role_configs.team_singletons" },
};

export function SaRoleConfigsPage() {
  const { t: tFlat } = useI18n();
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ["sa-role-configs"],
    queryFn: saApi.roleConfigs,
  });

  const grouped = useMemo(() => {
    const out: Record<RoleTeam, RoleConfig[]> = {
      civilians: [], mafia: [], singletons: [],
    };
    (data?.items ?? []).forEach((r) => out[r.team]?.push(r));
    TEAM_ORDER.forEach((team) =>
      out[team].sort((a, b) => a.order_idx - b.order_idx),
    );
    return out;
  }, [data]);

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;
  }

  return (
    <>
      <h2 style={{ marginTop: 0 }}>
        🎭 {t("admin.role_configs.title")}
      </h2>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 1rem" }}>
        {t("admin.role_configs.hint")}
      </p>

      {TEAM_ORDER.map((team) => (
        <section key={team} className="webapp-section">
          <h3>
            {TEAM_META[team].emoji} {t(TEAM_META[team].key)}{" "}
            <span style={{ color: "var(--muted)", fontWeight: 400 }}>
              ({grouped[team].length})
            </span>
          </h3>
          {grouped[team].map((cfg) => (
            <RoleCard key={cfg.role} cfg={cfg} />
          ))}
        </section>
      ))}
    </>
  );
}

function RoleCard({ cfg }: { cfg: RoleConfig }) {
  const { t } = useTranslation();
  const qc = useQueryClient();

  const [draft, setDraft] = useState<EditableFields>(() => extract(cfg));
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    setDraft(extract(cfg));
  }, [cfg]);

  const dirty = useMemo(() => !same(draft, cfg), [draft, cfg]);

  const mutation = useMutation({
    mutationFn: (patch: Partial<EditableFields>) =>
      saApi.updateRoleConfig(cfg.role, patch),
    onSuccess: () => {
      setSavedFlash(true);
      qc.invalidateQueries({ queryKey: ["sa-role-configs"] });
      setTimeout(() => setSavedFlash(false), 1400);
    },
  });

  const onSave = () => {
    if (!dirty) return;
    const patch: Partial<EditableFields> = {};
    (Object.keys(draft) as (keyof EditableFields)[]).forEach((k) => {
      if (draft[k] !== cfg[k]) patch[k] = draft[k];
    });
    mutation.mutate(patch);
  };

  const customSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <div
      className={`role-card ${savedFlash ? "flash" : ""}`}
      style={{
        padding: "0.75rem 0",
        borderBottom: "1px solid #2a2a45",
        display: "grid",
        gridTemplateColumns: "44px 1fr auto",
        gap: "0.75rem",
        alignItems: "center",
      }}
    >
      <div
        style={{
          fontSize: 28,
          textAlign: "center",
          lineHeight: 1,
        }}
        title={cfg.role}
      >
        {draft.static_emoji}
        {customSet && (
          <div
            style={{ fontSize: 10, color: "var(--accent)", marginTop: 2 }}
            title={t("admin.role_configs.has_custom")}
          >
            ★
          </div>
        )}
      </div>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            marginBottom: 4,
          }}
        >
          <strong style={{ fontSize: "0.95rem" }}>{draft.name_uz || cfg.role}</strong>
          <code style={{ color: "var(--muted)", fontSize: "0.7rem" }}>
            {cfg.role}
          </code>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 4,
            marginBottom: 4,
          }}
        >
          <LabelInput
            placeholder="🇺🇿"
            value={draft.name_uz}
            onChange={(v) => setDraft({ ...draft, name_uz: v })}
          />
          <LabelInput
            placeholder="🇷🇺"
            value={draft.name_ru}
            onChange={(v) => setDraft({ ...draft, name_ru: v })}
          />
          <LabelInput
            placeholder="🇬🇧"
            value={draft.name_en}
            onChange={(v) => setDraft({ ...draft, name_en: v })}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 4 }}>
          <input
            className="sa-input"
            style={{ width: 48, fontSize: 18, textAlign: "center" }}
            value={draft.static_emoji}
            onChange={(e) =>
              setDraft({ ...draft, static_emoji: e.target.value })
            }
          />
          <input
            className="sa-input"
            style={{ fontFamily: "monospace", fontSize: 12 }}
            placeholder={t("admin.role_configs.custom_id_placeholder")}
            value={draft.custom_emoji_id}
            onChange={(e) =>
              setDraft({ ...draft, custom_emoji_id: e.target.value })
            }
          />
        </div>

        {mutation.isError && (
          <div style={{ fontSize: 11, color: "tomato", marginTop: 4 }}>
            {(mutation.error as Error)?.message ?? "error"}
          </div>
        )}
      </div>

      <button
        className={`sa-chip ${dirty ? "active" : ""}`}
        disabled={!dirty || mutation.isPending}
        onClick={onSave}
        style={{ padding: "0.4rem 0.7rem" }}
        title={t("save")}
      >
        {mutation.isPending ? "⏳" : savedFlash ? "✅" : "💾"}
      </button>
    </div>
  );
}

function LabelInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      className="sa-input"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      style={{ fontSize: 12, padding: "0.3rem 0.4rem" }}
    />
  );
}

function extract(cfg: RoleConfig): EditableFields {
  return {
    name_uz: cfg.name_uz,
    name_ru: cfg.name_ru,
    name_en: cfg.name_en,
    static_emoji: cfg.static_emoji,
    custom_emoji_id: cfg.custom_emoji_id ?? "",
  };
}

function same(a: EditableFields, b: RoleConfig): boolean {
  return (
    a.name_uz === b.name_uz &&
    a.name_ru === b.name_ru &&
    a.name_en === b.name_en &&
    a.static_emoji === b.static_emoji &&
    a.custom_emoji_id === (b.custom_emoji_id ?? "")
  );
}
