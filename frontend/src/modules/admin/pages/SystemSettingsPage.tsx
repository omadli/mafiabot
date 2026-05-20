import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@shared/api/admin";

type Section = "item_prices" | "rewards" | "exchange" | "premium";

const ITEM_KEYS = [
  "shield", "killer_shield", "vote_shield",
  "rifle", "mask", "fake_document", "special_role",
];

export function SystemSettingsPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["admin-system-settings"],
    queryFn: adminApi.systemSettings,
  });

  const mutation = useMutation({
    mutationFn: (input: { section: Section; key: string; value: unknown }) =>
      adminApi.updateSystemSetting(input.section, input.key, input.value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-system-settings"] }),
  });

  if (isLoading || !data) {
    return <div style={{ padding: "2rem" }}>⏳ {t("loading")}</div>;
  }

  return (
    <>
      <h1 className="admin-page-title">⚙️ {t("admin.system_settings.title")}</h1>

      <section className="admin-card" style={{ marginBottom: "1.25rem" }}>
        <h2 className="admin-section-title">{t("admin.system_settings.prices")}</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t("admin.system_settings.col_item")}</th>
              <th style={{ textAlign: "right" }}>💵</th>
              <th style={{ textAlign: "right" }}>💎</th>
            </tr>
          </thead>
          <tbody>
            {ITEM_KEYS.map((code) => {
              const p = (data.item_prices as Record<string, { dollars: number; diamonds: number }>)[code] || {
                dollars: 0, diamonds: 0,
              };
              return (
                <tr key={code}>
                  <td>{t(`sa.system.item_${code}`, { defaultValue: code })}</td>
                  <td style={{ textAlign: "right" }}>
                    <NumInput
                      initial={p.dollars}
                      onSave={(v) =>
                        mutation.mutate({ section: "item_prices", key: `${code}.dollars`, value: v })
                      }
                    />
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <NumInput
                      initial={p.diamonds}
                      onSave={(v) =>
                        mutation.mutate({ section: "item_prices", key: `${code}.diamonds`, value: v })
                      }
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <SectionCard
        title={t("admin.system_settings.rewards")}
        data={data.rewards as Record<string, number>}
        section="rewards"
        prefix="reward"
        mutate={(k, v) => mutation.mutate({ section: "rewards", key: k, value: v })}
      />
      <SectionCard
        title={t("admin.system_settings.exchange")}
        data={Object.fromEntries(
          Object.entries(data.exchange as Record<string, number | boolean>).map(([k, v]) =>
            [k, typeof v === "boolean" ? (v ? 1 : 0) : v]
          )
        )}
        section="exchange"
        prefix="exchange"
        mutate={(k, v) => mutation.mutate({ section: "exchange", key: k, value: v })}
      />
      <SectionCard
        title={t("admin.system_settings.premium")}
        data={data.premium as Record<string, number>}
        section="premium"
        prefix="premium"
        mutate={(k, v) => mutation.mutate({ section: "premium", key: k, value: v })}
      />

      {data.updated_at && (
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 8 }}>
          🕒 {new Date(data.updated_at).toLocaleString()}
          {data.updated_by_tg_id && ` · ${t("sa.system.updated_by")}: ${data.updated_by_tg_id}`}
        </p>
      )}
    </>
  );
}

function SectionCard({
  title, data, prefix, mutate,
}: {
  title: string;
  data: Record<string, number>;
  section: Section;
  prefix: string;
  mutate: (k: string, v: number) => void;
}) {
  const { t } = useTranslation();
  return (
    <section className="admin-card" style={{ marginBottom: "1.25rem" }}>
      <h2 className="admin-section-title">{title}</h2>
      <table className="admin-table">
        <tbody>
          {Object.entries(data).map(([k, v]) => (
            <tr key={k}>
              <td style={{ width: "60%" }}>
                {t(`sa.system.${prefix}_${k}`, { defaultValue: k })}
                <div><code style={{ fontSize: 11, color: "var(--muted)" }}>{k}</code></div>
              </td>
              <td style={{ textAlign: "right" }}>
                <NumInput initial={Number(v)} onSave={(nv) => mutate(k, nv)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function NumInput({ initial, onSave }: { initial: number; onSave: (v: number) => void }) {
  const [val, setVal] = useState(String(initial));
  const dirty = parseInt(val || "0") !== initial;
  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
      <input
        type="number"
        className="admin-input"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        style={{ width: 90, textAlign: "right" }}
      />
      {dirty && (
        <button
          className="admin-btn primary"
          onClick={() => onSave(parseInt(val || "0"))}
          style={{ padding: "4px 10px", fontSize: 12 }}
        >
          ✓
        </button>
      )}
    </span>
  );
}
