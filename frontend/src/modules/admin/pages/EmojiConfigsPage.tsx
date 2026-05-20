import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@shared/api/admin";
import type { EmojiCategory, EmojiConfig } from "@shared/api/sa";

type Editable = Pick<
  EmojiConfig,
  "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id"
>;

const CATEGORY_META: Record<EmojiCategory, { emoji: string; key: string }> = {
  scene:    { emoji: "🎬", key: "admin.emoji_configs.cat_scene" },
  status:   { emoji: "💫", key: "admin.emoji_configs.cat_status" },
  item:     { emoji: "🛡", key: "admin.emoji_configs.cat_item" },
  action:   { emoji: "⚡",  key: "admin.emoji_configs.cat_action" },
  currency: { emoji: "💎", key: "admin.emoji_configs.cat_currency" },
};

const CAT_ORDER: EmojiCategory[] = ["scene", "status", "item", "action", "currency"];

export function EmojiConfigsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["admin-emoji-configs"],
    queryFn: adminApi.emojiConfigs,
  });

  const grouped = useMemo(() => {
    const out: Record<EmojiCategory, EmojiConfig[]> = {
      scene: [], status: [], item: [], action: [], currency: [],
    };
    (data?.items ?? []).forEach((r) => out[r.category]?.push(r));
    CAT_ORDER.forEach((c) => out[c].sort((a, b) => a.order_idx - b.order_idx));
    return out;
  }, [data]);

  return (
    <>
      <h1 className="admin-page-title">✨ {t("admin.emoji_configs.title")}</h1>
      <p className="admin-hint">{t("admin.emoji_configs.hint")}</p>

      {isLoading || !data ? (
        <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
      ) : (
        CAT_ORDER.map((cat) => (
          <section key={cat} style={{ marginBottom: "2rem" }}>
            <h2 className="admin-section-title">
              {CATEGORY_META[cat].emoji} {t(CATEGORY_META[cat].key)}{" "}
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                ({grouped[cat].length})
              </span>
            </h2>
            <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
              <table className="admin-table role-configs-table">
                <thead>
                  <tr>
                    <th style={{ width: 64 }}>{t("admin.role_configs.col_preview")}</th>
                    <th style={{ width: 180 }}>{t("admin.emoji_configs.col_code")}</th>
                    <th>🇺🇿</th>
                    <th>🇷🇺</th>
                    <th>🇬🇧</th>
                    <th style={{ width: 90 }}>{t("admin.role_configs.col_static")}</th>
                    <th style={{ width: 200 }}>{t("admin.role_configs.col_custom_id")}</th>
                    <th style={{ width: 100 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {grouped[cat].map((cfg) => (
                    <Row
                      key={cfg.code}
                      cfg={cfg}
                      onSaved={() =>
                        queryClient.invalidateQueries({ queryKey: ["admin-emoji-configs"] })
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

function Row({ cfg, onSaved }: { cfg: EmojiConfig; onSaved: () => void }) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<Editable>(() => extract(cfg));
  const [flash, setFlash] = useState(false);

  useEffect(() => setDraft(extract(cfg)), [cfg]);

  const dirty = useMemo(() => !same(draft, cfg), [draft, cfg]);

  const mutation = useMutation({
    mutationFn: (patch: Partial<Editable>) => adminApi.updateEmojiConfig(cfg.code, patch),
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

  const customSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <tr className={flash ? "row-saved-flash" : ""}>
      <td style={{ fontSize: 26, textAlign: "center" }}>
        {draft.static_emoji}
        {customSet && (
          <span style={{ marginLeft: 4, fontSize: 12, color: "var(--accent)" }}>★</span>
        )}
      </td>
      <td><code style={{ color: "var(--muted)" }}>{cfg.code}</code></td>
      <td>
        <input className="admin-input" value={draft.name_uz}
          onChange={(e) => setDraft({ ...draft, name_uz: e.target.value })} />
      </td>
      <td>
        <input className="admin-input" value={draft.name_ru}
          onChange={(e) => setDraft({ ...draft, name_ru: e.target.value })} />
      </td>
      <td>
        <input className="admin-input" value={draft.name_en}
          onChange={(e) => setDraft({ ...draft, name_en: e.target.value })} />
      </td>
      <td>
        <input className="admin-input"
          style={{ fontSize: 20, width: 56, textAlign: "center" }}
          value={draft.static_emoji}
          onChange={(e) => setDraft({ ...draft, static_emoji: e.target.value })} />
      </td>
      <td>
        <input className="admin-input"
          placeholder={t("admin.role_configs.custom_id_placeholder")}
          value={draft.custom_emoji_id}
          style={{ fontFamily: "monospace", fontSize: 12 }}
          onChange={(e) => setDraft({ ...draft, custom_emoji_id: e.target.value })} />
      </td>
      <td>
        <button className={`admin-btn ${dirty ? "primary" : ""}`}
          disabled={!dirty || mutation.isPending} onClick={onSave}>
          {mutation.isPending ? "⏳" : flash ? `✅ ${t("admin.role_configs.saved")}` : `💾 ${t("save")}`}
        </button>
      </td>
    </tr>
  );
}

function extract(c: EmojiConfig): Editable {
  return {
    name_uz: c.name_uz, name_ru: c.name_ru, name_en: c.name_en,
    static_emoji: c.static_emoji,
    custom_emoji_id: c.custom_emoji_id ?? "",
  };
}

function same(a: Editable, b: EmojiConfig): boolean {
  return a.name_uz === b.name_uz && a.name_ru === b.name_ru && a.name_en === b.name_en
      && a.static_emoji === b.static_emoji
      && a.custom_emoji_id === (b.custom_emoji_id ?? "");
}
