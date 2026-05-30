/**
 * Editable role-config registry — 21 roles grouped by team
 * (civilians / mafia / singletons). The bot resolves the i18n
 * `role-*` keys through these rows, so editing here is the only
 * way to localise role names without a redeploy.
 *
 * Combined from admin/RoleConfigsPage (table layout) and
 * webapp/SaRoleConfigsPage (mobile card layout). Layout chosen by
 * `surface` so each shell gets the form factor it expects. The
 * per-row edit hook is shared so both layouts get the same
 * save / dirty / flash semantics.
 *
 * Auth routes through superAdminApi.roleConfigs /
 * .updateRoleConfig → /api/{admin|sa}/role-configs/...
 */

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { Flag } from "@shared/components/Flag";
import {
  superAdminApi,
  type RoleConfig,
  type RoleTeam,
} from "@shared/api/superAdmin";

import { useSa } from "../context";

type Editable = Pick<
  RoleConfig,
  "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id"
>;

const TEAM_ORDER: RoleTeam[] = ["civilians", "mafia", "singletons"];

const TEAM_LABEL: Record<RoleTeam, { emoji: string; key: string }> = {
  civilians: { emoji: "👨‍👨‍👧‍👦", key: "admin.role_configs.team_civilians" },
  mafia: { emoji: "🤵🏼", key: "admin.role_configs.team_mafia" },
  singletons: { emoji: "🎯", key: "admin.role_configs.team_singletons" },
};

export function RoleConfigsPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const qc = useQueryClient();
  const isAdmin = surface === "admin";

  const { data, isLoading } = useQuery({
    queryKey: ["sa-role-configs"],
    queryFn: superAdminApi.roleConfigs,
  });

  const grouped = useMemo(() => {
    const out: Record<RoleTeam, RoleConfig[]> = {
      civilians: [],
      mafia: [],
      singletons: [],
    };
    (data?.items ?? []).forEach((r) => out[r.team]?.push(r));
    TEAM_ORDER.forEach((team) =>
      out[team].sort((a, b) => a.order_idx - b.order_idx),
    );
    return out;
  }, [data]);

  const onSaved = () =>
    qc.invalidateQueries({ queryKey: ["sa-role-configs"] });

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">🎭 {t("admin.role_configs.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>🎭 {t("admin.role_configs.title")}</h2>
  );

  if (isLoading || !data) {
    return (
      <>
        {titleEl}
        <div
          className={isAdmin ? "admin-card" : "webapp-section"}
          style={{ padding: "2rem", textAlign: "center" }}
        >
          ⏳ {t("loading")}
        </div>
      </>
    );
  }

  return (
    <>
      {titleEl}
      <p
        className={isAdmin ? "admin-hint" : undefined}
        style={
          !isAdmin
            ? { color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 1rem" }
            : undefined
        }
      >
        {t("admin.role_configs.hint")}
      </p>

      {TEAM_ORDER.map((team) => (
        <section
          key={team}
          style={{ marginBottom: isAdmin ? "2rem" : "0.6rem" }}
          className={!isAdmin ? "webapp-section" : undefined}
        >
          {isAdmin ? (
            <h2 className="admin-section-title">
              {TEAM_LABEL[team].emoji} {t(TEAM_LABEL[team].key)}{" "}
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                ({grouped[team].length})
              </span>
            </h2>
          ) : (
            <h3>
              {TEAM_LABEL[team].emoji} {t(TEAM_LABEL[team].key)}{" "}
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                ({grouped[team].length})
              </span>
            </h3>
          )}

          {isAdmin ? (
            <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
              <table className="admin-table role-configs-table">
                <thead>
                  <tr>
                    <th style={{ width: 80 }}>
                      {t("admin.role_configs.col_preview")}
                    </th>
                    <th style={{ width: 80 }}>
                      {t("admin.role_configs.col_role")}
                    </th>
                    <th>
                      <Flag lang="uz" /> {t("admin.role_configs.col_name_uz")}
                    </th>
                    <th>
                      <Flag lang="ru" /> {t("admin.role_configs.col_name_ru")}
                    </th>
                    <th>
                      <Flag lang="en" /> {t("admin.role_configs.col_name_en")}
                    </th>
                    <th style={{ width: 100 }}>
                      {t("admin.role_configs.col_static")}
                    </th>
                    <th style={{ width: 200 }}>
                      {t("admin.role_configs.col_custom_id")}
                    </th>
                    <th style={{ width: 100 }} />
                  </tr>
                </thead>
                <tbody>
                  {grouped[team].map((cfg) => (
                    <TableRow key={cfg.role} cfg={cfg} onSaved={onSaved} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            grouped[team].map((cfg) => (
              <CardRow key={cfg.role} cfg={cfg} onSaved={onSaved} />
            ))
          )}
        </section>
      ))}
    </>
  );
}

// === Shared per-row edit hook ===

function useRowEdit(cfg: RoleConfig, onSaved: () => void) {
  const [draft, setDraft] = useState<Editable>(() => extract(cfg));
  const [flash, setFlash] = useState(false);

  // Re-seed when the upstream row changes (e.g. concurrent edit
  // elsewhere); the local draft is dropped only when the server
  // moves past us.
  useEffect(() => setDraft(extract(cfg)), [cfg]);

  const dirty = useMemo(() => !same(draft, cfg), [draft, cfg]);

  const mutation = useMutation({
    mutationFn: (patch: Partial<Editable>) =>
      superAdminApi.updateRoleConfig(cfg.role, patch),
    onSuccess: () => {
      setFlash(true);
      onSaved();
      setTimeout(() => setFlash(false), 1400);
    },
  });

  const onSave = () => {
    if (!dirty) return;
    const patch: Partial<Editable> = {};
    (Object.keys(draft) as (keyof Editable)[]).forEach((k) => {
      if (draft[k] !== cfg[k]) patch[k] = draft[k];
    });
    mutation.mutate(patch);
  };

  return { draft, setDraft, dirty, flash, mutation, onSave };
}

// === Admin: desktop table row ===

function TableRow({ cfg, onSaved }: { cfg: RoleConfig; onSaved: () => void }) {
  const { t } = useTranslation();
  const { draft, setDraft, dirty, flash, mutation, onSave } = useRowEdit(cfg, onSaved);
  const customIdSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <tr className={flash ? "row-saved-flash" : ""}>
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
          onChange={(e) =>
            setDraft({ ...draft, static_emoji: e.target.value })
          }
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
          type="button"
          className={`admin-btn ${dirty ? "primary" : ""}`}
          disabled={!dirty || mutation.isPending}
          onClick={onSave}
        >
          {mutation.isPending
            ? "⏳"
            : flash
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

// === WebApp: mobile card row ===

function CardRow({ cfg, onSaved }: { cfg: RoleConfig; onSaved: () => void }) {
  const { t } = useTranslation();
  const { draft, setDraft, dirty, flash, mutation, onSave } = useRowEdit(cfg, onSaved);
  const customIdSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <div className={`sa-config-row ${flash ? "flash" : ""}`}>
      <div style={{ fontSize: 26, textAlign: "center" }}>
        {draft.static_emoji}
        {customIdSet && (
          <div style={{ fontSize: 10, color: "var(--accent)" }}>★</div>
        )}
      </div>
      <div className="sa-config-row-editor">
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <strong style={{ fontSize: 13 }}>{draft.name_uz || cfg.role}</strong>
          <code style={{ color: "var(--muted)", fontSize: 10 }}>{cfg.role}</code>
        </div>
        <div className="sa-config-row-langs">
          <input
            className="sa-input"
            style={{ fontSize: 12, padding: "3px 5px" }}
            placeholder="🇺🇿"
            value={draft.name_uz}
            onChange={(e) => setDraft({ ...draft, name_uz: e.target.value })}
          />
          <input
            className="sa-input"
            style={{ fontSize: 12, padding: "3px 5px" }}
            placeholder="🇷🇺"
            value={draft.name_ru}
            onChange={(e) => setDraft({ ...draft, name_ru: e.target.value })}
          />
          <input
            className="sa-input"
            style={{ fontSize: 12, padding: "3px 5px" }}
            placeholder="🇬🇧"
            value={draft.name_en}
            onChange={(e) => setDraft({ ...draft, name_en: e.target.value })}
          />
        </div>
        <div className="sa-config-row-extras">
          <input
            className="sa-input"
            style={{
              width: 44,
              textAlign: "center",
              fontSize: 16,
              padding: "3px 4px",
            }}
            value={draft.static_emoji}
            onChange={(e) =>
              setDraft({ ...draft, static_emoji: e.target.value })
            }
          />
          <input
            className="sa-input"
            style={{ fontFamily: "monospace", fontSize: 11, padding: "3px 6px" }}
            placeholder={t("admin.role_configs.custom_id_placeholder")}
            value={draft.custom_emoji_id}
            onChange={(e) =>
              setDraft({ ...draft, custom_emoji_id: e.target.value })
            }
          />
        </div>
      </div>
      <button
        type="button"
        className={`sa-chip ${dirty ? "active" : ""}`}
        disabled={!dirty || mutation.isPending}
        onClick={onSave}
        style={{ padding: "0.4rem 0.7rem" }}
        title={t("save")}
      >
        {mutation.isPending ? "⏳" : flash ? "✅" : "💾"}
      </button>
    </div>
  );
}

// === Pure helpers ===

function extract(c: RoleConfig): Editable {
  return {
    name_uz: c.name_uz,
    name_ru: c.name_ru,
    name_en: c.name_en,
    static_emoji: c.static_emoji,
    custom_emoji_id: c.custom_emoji_id ?? "",
  };
}

function same(a: Editable, b: RoleConfig): boolean {
  return (
    a.name_uz === b.name_uz &&
    a.name_ru === b.name_ru &&
    a.name_en === b.name_en &&
    a.static_emoji === b.static_emoji &&
    a.custom_emoji_id === (b.custom_emoji_id ?? "")
  );
}
