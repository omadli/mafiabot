import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@shared/api/admin";
import type { RoleConfig, RoleTeam } from "@shared/api/sa";

type EditableFields = Pick<
  RoleConfig,
  "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id"
>;

const TEAM_LABEL: Record<RoleTeam, { emoji: string; key: string }> = {
  civilians:  { emoji: "👨‍👨‍👧‍👦", key: "admin.role_configs.team_civilians" },
  mafia:      { emoji: "🤵🏼",  key: "admin.role_configs.team_mafia" },
  singletons: { emoji: "🎯",   key: "admin.role_configs.team_singletons" },
};

const TEAM_ORDER: RoleTeam[] = ["civilians", "mafia", "singletons"];

export function RoleConfigsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["role-configs"],
    queryFn: adminApi.roleConfigs,
  });

  const grouped = useMemo(() => {
    const out: Record<RoleTeam, RoleConfig[]> = {
      civilians: [],
      mafia: [],
      singletons: [],
    };
    (data?.items ?? []).forEach((r) => {
      out[r.team]?.push(r);
    });
    TEAM_ORDER.forEach((team) =>
      out[team].sort((a, b) => a.order_idx - b.order_idx),
    );
    return out;
  }, [data]);

  return (
    <>
      <h1 className="admin-page-title">
        🎭 {t("admin.role_configs.title")}
      </h1>
      <p className="admin-hint">{t("admin.role_configs.hint")}</p>

      {isLoading || !data ? (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          ⏳ {t("loading")}
        </div>
      ) : (
        TEAM_ORDER.map((team) => (
          <section key={team} style={{ marginBottom: "2rem" }}>
            <h2 className="admin-section-title">
              {TEAM_LABEL[team].emoji} {t(TEAM_LABEL[team].key)}{" "}
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                ({grouped[team].length})
              </span>
            </h2>
            <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
              <table className="admin-table role-configs-table">
                <thead>
                  <tr>
                    <th style={{ width: 80 }}>{t("admin.role_configs.col_preview")}</th>
                    <th style={{ width: 80 }}>{t("admin.role_configs.col_role")}</th>
                    <th>🇺🇿 {t("admin.role_configs.col_name_uz")}</th>
                    <th>🇷🇺 {t("admin.role_configs.col_name_ru")}</th>
                    <th>🇬🇧 {t("admin.role_configs.col_name_en")}</th>
                    <th style={{ width: 100 }}>
                      {t("admin.role_configs.col_static")}
                    </th>
                    <th style={{ width: 200 }}>
                      {t("admin.role_configs.col_custom_id")}
                    </th>
                    <th style={{ width: 100 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {grouped[team].map((cfg) => (
                    <RoleConfigRow
                      key={cfg.role}
                      cfg={cfg}
                      onSaved={() =>
                        queryClient.invalidateQueries({ queryKey: ["role-configs"] })
                      }
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))
      )}
    </>
  );
}

interface RowProps {
  cfg: RoleConfig;
  onSaved: () => void;
}

function RoleConfigRow({ cfg, onSaved }: RowProps) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<EditableFields>(() => extractEditable(cfg));
  const [savedFlash, setSavedFlash] = useState(false);

  // If parent data refreshes, reset draft when row identity hasn't been edited
  useEffect(() => {
    setDraft(extractEditable(cfg));
  }, [cfg]);

  const dirty = useMemo(() => !sameEditable(draft, cfg), [draft, cfg]);

  const mutation = useMutation({
    mutationFn: (patch: Partial<EditableFields>) =>
      adminApi.updateRoleConfig(cfg.role, patch),
    onSuccess: () => {
      setSavedFlash(true);
      onSaved();
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

  const customIdSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <tr className={savedFlash ? "row-saved-flash" : ""}>
      <td style={{ fontSize: 28, textAlign: "center" }}>
        {draft.static_emoji}
        {customIdSet && (
          <span
            title={t("admin.role_configs.has_custom")}
            style={{ marginLeft: 4, fontSize: 12 }}
          >
            ★
          </span>
        )}
      </td>
      <td>
        <code style={{ color: "var(--muted)" }}>{cfg.role}</code>
      </td>
      <td>
        <input
          className="admin-input"
          value={draft.name_uz}
          onChange={(e) => setDraft({ ...draft, name_uz: e.target.value })}
        />
      </td>
      <td>
        <input
          className="admin-input"
          value={draft.name_ru}
          onChange={(e) => setDraft({ ...draft, name_ru: e.target.value })}
        />
      </td>
      <td>
        <input
          className="admin-input"
          value={draft.name_en}
          onChange={(e) => setDraft({ ...draft, name_en: e.target.value })}
        />
      </td>
      <td>
        <input
          className="admin-input"
          style={{ fontSize: 20, width: 56, textAlign: "center" }}
          value={draft.static_emoji}
          onChange={(e) => setDraft({ ...draft, static_emoji: e.target.value })}
        />
      </td>
      <td>
        <input
          className="admin-input"
          placeholder={t("admin.role_configs.custom_id_placeholder")}
          value={draft.custom_emoji_id}
          onChange={(e) =>
            setDraft({ ...draft, custom_emoji_id: e.target.value })
          }
          style={{ fontFamily: "monospace", fontSize: 12 }}
        />
      </td>
      <td>
        <button
          className={`admin-btn ${dirty ? "primary" : ""}`}
          disabled={!dirty || mutation.isPending}
          onClick={onSave}
        >
          {mutation.isPending
            ? "⏳"
            : savedFlash
              ? `✅ ${t("admin.role_configs.saved")}`
              : `💾 ${t("save")}`}
        </button>
        {mutation.isError && (
          <div style={{ fontSize: 11, color: "var(--danger, #d33)" }}>
            {(mutation.error as Error)?.message ?? t("error")}
          </div>
        )}
      </td>
    </tr>
  );
}

function extractEditable(cfg: RoleConfig): EditableFields {
  return {
    name_uz: cfg.name_uz,
    name_ru: cfg.name_ru,
    name_en: cfg.name_en,
    static_emoji: cfg.static_emoji,
    custom_emoji_id: cfg.custom_emoji_id ?? "",
  };
}

function sameEditable(a: EditableFields, b: RoleConfig): boolean {
  return (
    a.name_uz === b.name_uz &&
    a.name_ru === b.name_ru &&
    a.name_en === b.name_en &&
    a.static_emoji === b.static_emoji &&
    a.custom_emoji_id === (b.custom_emoji_id ?? "")
  );
}
