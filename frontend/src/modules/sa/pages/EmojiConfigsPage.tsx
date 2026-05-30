/**
 * Editable emoji-config registry (5 categories: scene, status, item,
 * action, currency). Each row's name_uz / name_ru / name_en plus
 * static_emoji and custom_emoji_id are editable; the bot's
 * `<e:slug>` placeables substitute these at render time.
 *
 * Combined from admin/EmojiConfigsPage (table layout, sortable
 * columns, language flag headers) and webapp/SaEmojiConfigsPage
 * (mobile-friendly card rows). Picks the layout based on `surface`
 * so the desktop site gets the wider table and Telegram WebApp
 * stays usable on a narrow viewport.
 *
 * Auth routes through superAdminApi.emojiConfigs /
 * .updateEmojiConfig → /api/{admin|sa}/emoji-configs/...
 */

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { Flag } from "@shared/components/Flag";
import {
  superAdminApi,
  type EmojiCategory,
  type EmojiConfig,
} from "@shared/api/superAdmin";

import { useSa } from "../context";

type Editable = Pick<
  EmojiConfig,
  "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id"
>;

const CAT_ORDER: EmojiCategory[] = ["scene", "status", "item", "action", "currency"];

const CATEGORY_META: Record<EmojiCategory, { emoji: string; key: string }> = {
  scene: { emoji: "🎬", key: "admin.emoji_configs.cat_scene" },
  status: { emoji: "💫", key: "admin.emoji_configs.cat_status" },
  item: { emoji: "🛡", key: "admin.emoji_configs.cat_item" },
  action: { emoji: "⚡", key: "admin.emoji_configs.cat_action" },
  currency: { emoji: "💎", key: "admin.emoji_configs.cat_currency" },
};

export function EmojiConfigsPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const qc = useQueryClient();

  const isAdmin = surface === "admin";

  const { data, isLoading } = useQuery({
    queryKey: ["sa-emoji-configs"],
    queryFn: superAdminApi.emojiConfigs,
  });

  const grouped = useMemo(() => {
    const out: Record<EmojiCategory, EmojiConfig[]> = {
      scene: [],
      status: [],
      item: [],
      action: [],
      currency: [],
    };
    (data?.items ?? []).forEach((r) => out[r.category]?.push(r));
    CAT_ORDER.forEach((c) => out[c].sort((a, b) => a.order_idx - b.order_idx));
    return out;
  }, [data]);

  const onSaved = () =>
    qc.invalidateQueries({ queryKey: ["sa-emoji-configs"] });

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">✨ {t("admin.emoji_configs.title")}</h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>✨ {t("admin.emoji_configs.title")}</h2>
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
        {t("admin.emoji_configs.hint")}
      </p>

      {CAT_ORDER.map((cat) => (
        <section
          key={cat}
          style={{ marginBottom: isAdmin ? "2rem" : "0.6rem" }}
          className={!isAdmin ? "webapp-section" : undefined}
        >
          {isAdmin ? (
            <h2 className="admin-section-title">
              {CATEGORY_META[cat].emoji} {t(CATEGORY_META[cat].key)}{" "}
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                ({grouped[cat].length})
              </span>
            </h2>
          ) : (
            <h3>
              {CATEGORY_META[cat].emoji} {t(CATEGORY_META[cat].key)}{" "}
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                ({grouped[cat].length})
              </span>
            </h3>
          )}

          {isAdmin ? (
            <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
              <table className="admin-table role-configs-table">
                <thead>
                  <tr>
                    <th style={{ width: 64 }}>
                      {t("admin.role_configs.col_preview")}
                    </th>
                    <th style={{ width: 180 }}>
                      {t("admin.emoji_configs.col_code")}
                    </th>
                    <th>
                      <Flag lang="uz" />
                    </th>
                    <th>
                      <Flag lang="ru" />
                    </th>
                    <th>
                      <Flag lang="en" />
                    </th>
                    <th style={{ width: 90 }}>
                      {t("admin.role_configs.col_static")}
                    </th>
                    <th style={{ width: 200 }}>
                      {t("admin.role_configs.col_custom_id")}
                    </th>
                    <th style={{ width: 100 }} />
                  </tr>
                </thead>
                <tbody>
                  {grouped[cat].map((cfg) => (
                    <TableRow key={cfg.code} cfg={cfg} onSaved={onSaved} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            grouped[cat].map((cfg) => (
              <CardRow key={cfg.code} cfg={cfg} onSaved={onSaved} />
            ))
          )}
        </section>
      ))}
    </>
  );
}

// === Shared per-row state hook ===

function useRowEdit(cfg: EmojiConfig, onSaved: () => void) {
  const [draft, setDraft] = useState<Editable>(() => extract(cfg));
  const [flash, setFlash] = useState(false);

  // Re-seed when the upstream config changes (e.g. another tab saved
  // the same row); discard the draft only when the server moved past us.
  useEffect(() => setDraft(extract(cfg)), [cfg]);

  const dirty = useMemo(() => !same(draft, cfg), [draft, cfg]);

  const mutation = useMutation({
    mutationFn: (patch: Partial<Editable>) =>
      superAdminApi.updateEmojiConfig(cfg.code, patch),
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

function TableRow({ cfg, onSaved }: { cfg: EmojiConfig; onSaved: () => void }) {
  const { t } = useTranslation();
  const { draft, setDraft, dirty, flash, mutation, onSave } = useRowEdit(cfg, onSaved);
  const customSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <tr className={flash ? "row-saved-flash" : ""}>
      <td style={{ fontSize: 26, textAlign: "center" }}>
        {draft.static_emoji}
        {customSet && (
          <span style={{ marginLeft: 4, fontSize: 12, color: "var(--accent)" }}>★</span>
        )}
      </td>
      <td>
        <code style={{ color: "var(--muted)" }}>{cfg.code}</code>
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
          style={{ fontFamily: "monospace", fontSize: 12 }}
          onChange={(e) =>
            setDraft({ ...draft, custom_emoji_id: e.target.value })
          }
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
      </td>
    </tr>
  );
}

// === WebApp: mobile card row ===

function CardRow({ cfg, onSaved }: { cfg: EmojiConfig; onSaved: () => void }) {
  const { t } = useTranslation();
  const { draft, setDraft, dirty, flash, mutation, onSave } = useRowEdit(cfg, onSaved);
  const customSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <div className={`sa-config-row ${flash ? "flash" : ""}`}>
      <div style={{ fontSize: 24, textAlign: "center" }}>
        {draft.static_emoji}
        {customSet && (
          <div style={{ fontSize: 10, color: "var(--accent)" }}>★</div>
        )}
      </div>
      <div className="sa-config-row-editor">
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <strong style={{ fontSize: 13 }}>{draft.name_uz || cfg.code}</strong>
          <code style={{ color: "var(--muted)", fontSize: 10 }}>{cfg.code}</code>
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

function extract(c: EmojiConfig): Editable {
  return {
    name_uz: c.name_uz,
    name_ru: c.name_ru,
    name_en: c.name_en,
    static_emoji: c.static_emoji,
    custom_emoji_id: c.custom_emoji_id ?? "",
  };
}

function same(a: Editable, b: EmojiConfig): boolean {
  return (
    a.name_uz === b.name_uz &&
    a.name_ru === b.name_ru &&
    a.name_en === b.name_en &&
    a.static_emoji === b.static_emoji &&
    a.custom_emoji_id === (b.custom_emoji_id ?? "")
  );
}
