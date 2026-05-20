import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi, type EmojiCategory, type EmojiConfig } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

type Editable = Pick<
  EmojiConfig,
  "name_uz" | "name_ru" | "name_en" | "static_emoji" | "custom_emoji_id"
>;

const CAT_ORDER: EmojiCategory[] = ["scene", "status", "item", "action", "currency"];

const CATEGORY_META: Record<EmojiCategory, { emoji: string; key: string }> = {
  scene:    { emoji: "🎬", key: "admin.emoji_configs.cat_scene" },
  status:   { emoji: "💫", key: "admin.emoji_configs.cat_status" },
  item:     { emoji: "🛡", key: "admin.emoji_configs.cat_item" },
  action:   { emoji: "⚡",  key: "admin.emoji_configs.cat_action" },
  currency: { emoji: "💎", key: "admin.emoji_configs.cat_currency" },
};

export function SaEmojiConfigsPage() {
  const { t: tFlat } = useI18n();
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ["sa-emoji-configs"],
    queryFn: saApi.emojiConfigs,
  });

  const grouped = useMemo(() => {
    const out: Record<EmojiCategory, EmojiConfig[]> = {
      scene: [], status: [], item: [], action: [], currency: [],
    };
    (data?.items ?? []).forEach((r) => out[r.category]?.push(r));
    CAT_ORDER.forEach((c) => out[c].sort((a, b) => a.order_idx - b.order_idx));
    return out;
  }, [data]);

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {tFlat("loading")}</div>;
  }

  return (
    <>
      <h2 style={{ marginTop: 0 }}>✨ {t("admin.emoji_configs.title")}</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 1rem" }}>
        {t("admin.emoji_configs.hint")}
      </p>

      {CAT_ORDER.map((cat) => (
        <section key={cat} className="webapp-section">
          <h3>
            {CATEGORY_META[cat].emoji} {t(CATEGORY_META[cat].key)}{" "}
            <span style={{ color: "var(--muted)", fontWeight: 400 }}>
              ({grouped[cat].length})
            </span>
          </h3>
          {grouped[cat].map((cfg) => <Row key={cfg.code} cfg={cfg} />)}
        </section>
      ))}
    </>
  );
}

function Row({ cfg }: { cfg: EmojiConfig }) {
  const { t } = useTranslation();
  const qc = useQueryClient();

  const [draft, setDraft] = useState<Editable>(() => extract(cfg));
  const [flash, setFlash] = useState(false);

  useEffect(() => setDraft(extract(cfg)), [cfg]);
  const dirty = useMemo(() => !same(draft, cfg), [draft, cfg]);

  const mut = useMutation({
    mutationFn: (patch: Partial<Editable>) => saApi.updateEmojiConfig(cfg.code, patch),
    onSuccess: () => {
      setFlash(true);
      qc.invalidateQueries({ queryKey: ["sa-emoji-configs"] });
      setTimeout(() => setFlash(false), 1400);
    },
  });

  const onSave = () => {
    if (!dirty) return;
    const patch: Partial<Editable> = {};
    (Object.keys(draft) as (keyof Editable)[]).forEach((k) => {
      if (draft[k] !== cfg[k]) patch[k] = draft[k];
    });
    mut.mutate(patch);
  };

  const customSet = draft.custom_emoji_id.trim().length > 0;

  return (
    <div
      className={flash ? "flash" : ""}
      style={{
        padding: "0.6rem 0",
        borderBottom: "1px solid #2a2a45",
        display: "grid",
        gridTemplateColumns: "40px 1fr auto",
        gap: 8,
        alignItems: "center",
      }}
    >
      <div style={{ fontSize: 24, textAlign: "center" }}>
        {draft.static_emoji}
        {customSet && <div style={{ fontSize: 10, color: "var(--accent)" }}>★</div>}
      </div>
      <div style={{ minWidth: 0, display: "grid", gap: 4 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <strong style={{ fontSize: 13 }}>{draft.name_uz || cfg.code}</strong>
          <code style={{ color: "var(--muted)", fontSize: 10 }}>{cfg.code}</code>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 4 }}>
          <input className="sa-input" style={{ fontSize: 12, padding: "3px 5px" }}
            placeholder="🇺🇿" value={draft.name_uz}
            onChange={(e) => setDraft({ ...draft, name_uz: e.target.value })} />
          <input className="sa-input" style={{ fontSize: 12, padding: "3px 5px" }}
            placeholder="🇷🇺" value={draft.name_ru}
            onChange={(e) => setDraft({ ...draft, name_ru: e.target.value })} />
          <input className="sa-input" style={{ fontSize: 12, padding: "3px 5px" }}
            placeholder="🇬🇧" value={draft.name_en}
            onChange={(e) => setDraft({ ...draft, name_en: e.target.value })} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "44px 1fr", gap: 4 }}>
          <input className="sa-input" style={{ width: 44, textAlign: "center", fontSize: 16, padding: "3px 4px" }}
            value={draft.static_emoji}
            onChange={(e) => setDraft({ ...draft, static_emoji: e.target.value })} />
          <input className="sa-input" style={{ fontFamily: "monospace", fontSize: 11, padding: "3px 6px" }}
            placeholder={t("admin.role_configs.custom_id_placeholder")}
            value={draft.custom_emoji_id}
            onChange={(e) => setDraft({ ...draft, custom_emoji_id: e.target.value })} />
        </div>
      </div>
      <button className={`sa-chip ${dirty ? "active" : ""}`}
        disabled={!dirty || mut.isPending} onClick={onSave}
        style={{ padding: "0.4rem 0.7rem" }} title={t("save")}>
        {mut.isPending ? "⏳" : flash ? "✅" : "💾"}
      </button>
    </div>
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
