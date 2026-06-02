/**
 * Unified system settings page.
 *
 * Combined from admin/SystemSettingsPage (3-col table layout per
 * section, fixed ITEM_KEYS list) and webapp/SaSystemPage (entry-
 * based iteration that follows whatever the backend returns). The
 * webapp's flexible iteration wins because new settings will appear
 * automatically without code changes — the admin's hard-coded
 * ITEM_KEYS was the legacy shape.
 *
 * Surface drives layout only: `admin-card` + `admin-table` chrome
 * on the desktop, stacked `webapp-section` rows on the Mini App.
 * Both surfaces share the DiamondPackagesEditor for Stars-tier
 * pricing.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import {
  superAdminApi,
  type DiamondPackage,
} from "@shared/api/superAdmin";

import { DiamondPackagesEditor } from "../components/DiamondPackagesEditor";
import { useSa } from "../context";

type Section = "item_prices" | "rewards" | "exchange" | "premium";

export function SystemSettingsPage() {
  const { t } = useTranslation();
  const { surface } = useSa();
  const isAdmin = surface === "admin";
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["sa-system-settings"],
    queryFn: superAdminApi.systemSettings,
  });

  const mutation = useMutation({
    mutationFn: (input: { section: Section; key: string; value: unknown }) =>
      superAdminApi.updateSystemSetting(input.section, input.key, input.value),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["sa-system-settings"] }),
  });

  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  if (isLoading || !data) {
    return <div className={cardCls}>⏳ {t("loading")}</div>;
  }

  const titleEl = isAdmin ? (
    <h1 className="admin-page-title">
      ⚙️ {t("sa.system.title", "System settings")}
    </h1>
  ) : (
    <h2 style={{ marginTop: 0 }}>
      ⚙️ {t("sa.system.title", "System settings")}
    </h2>
  );

  return (
    <>
      {titleEl}

      <ItemPricesSection
        data={data.item_prices as Record<string, { dollars: number; diamonds: number }>}
        surface={surface}
        mutate={(key, value) => mutation.mutate({ section: "item_prices", key, value })}
      />

      <SectionCard
        title={t("sa.system.rewards", "Rewards")}
        prefix="reward"
        surface={surface}
        data={data.rewards as Record<string, number>}
        mutate={(key, value) => mutation.mutate({ section: "rewards", key, value })}
      />

      <SectionCard
        title={t("sa.system.exchange", "Exchange")}
        prefix="exchange"
        surface={surface}
        data={Object.fromEntries(
          Object.entries(
            data.exchange as Record<string, number | boolean>,
          ).map(([k, v]) => [k, typeof v === "boolean" ? (v ? 1 : 0) : v]),
        )}
        mutate={(key, value) => mutation.mutate({ section: "exchange", key, value })}
      />

      <SectionCard
        title={t("sa.system.premium", "Premium")}
        prefix="premium"
        surface={surface}
        data={data.premium as Record<string, number>}
        mutate={(key, value) => mutation.mutate({ section: "premium", key, value })}
      />

      <DiamondPackagesEditor
        initial={
          ((data as unknown as { diamond_packages?: DiamondPackage[] })
            .diamond_packages ?? []) as DiamondPackage[]
        }
      />

      {data.updated_at && (
        <p
          style={{
            color: "var(--muted)",
            fontSize: isAdmin ? "0.85rem" : "0.8rem",
            marginTop: 8,
          }}
        >
          🕒 {new Date(data.updated_at).toLocaleString()}
          {data.updated_by_tg_id &&
            ` · ${t("sa.system.updated_by", "by")}: ${String(data.updated_by_tg_id)}`}
        </p>
      )}
    </>
  );
}

// === Sections ===

function ItemPricesSection({
  data,
  surface,
  mutate,
}: {
  data: Record<string, { dollars: number; diamonds: number }>;
  surface: "admin" | "webapp";
  mutate: (key: string, value: number) => void;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";
  const tableCls = isAdmin ? "admin-table" : "sa-table";

  return (
    <section className={cardCls} style={{ marginBottom: "1.25rem" }}>
      <h3 className={isAdmin ? "admin-section-title" : undefined}>
        {t("sa.system.prices", "Item prices")}
      </h3>
      <table className={tableCls}>
        <thead>
          <tr>
            <th>{t("sa.system.col_item", "Item")}</th>
            <th style={{ textAlign: "right" }}>
              {isAdmin ? "💵" : t("sa.system.col_dollars", "Dollars")}
            </th>
            <th style={{ textAlign: "right" }}>
              {isAdmin ? "💎" : t("sa.system.col_diamonds", "Diamonds")}
            </th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([code, p]) => (
            <tr key={code}>
              <td>{t(`sa.system.item_${code}`, { defaultValue: code })}</td>
              <td style={{ textAlign: "right" }}>
                <NumInput
                  surface={surface}
                  initial={p.dollars}
                  onSave={(v) => mutate(`${code}.dollars`, v)}
                />
              </td>
              <td style={{ textAlign: "right" }}>
                <NumInput
                  surface={surface}
                  initial={p.diamonds}
                  onSave={(v) => mutate(`${code}.diamonds`, v)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function SectionCard({
  title,
  prefix,
  surface,
  data,
  mutate,
}: {
  title: string;
  prefix: string;
  surface: "admin" | "webapp";
  data: Record<string, number>;
  mutate: (key: string, value: number) => void;
}) {
  const { t } = useTranslation();
  const isAdmin = surface === "admin";
  const cardCls = isAdmin ? "admin-card" : "webapp-section";

  if (isAdmin) {
    return (
      <section className={cardCls} style={{ marginBottom: "1.25rem" }}>
        <h3 className="admin-section-title">{title}</h3>
        <table className="admin-table">
          <tbody>
            {Object.entries(data).map(([k, v]) => (
              <tr key={k}>
                <td style={{ width: "60%" }}>
                  {t(`sa.system.${prefix}_${k}`, { defaultValue: k })}
                  <div>
                    <code style={{ fontSize: 11, color: "var(--muted)" }}>{k}</code>
                  </div>
                </td>
                <td style={{ textAlign: "right" }}>
                  <NumInput
                    surface={surface}
                    initial={Number(v)}
                    onSave={(nv) => mutate(k, nv)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    );
  }

  return (
    <div className={cardCls}>
      <h3>{title}</h3>
      {Object.entries(data).map(([k, v]) => (
        <SettingRow
          key={k}
          label={t(`sa.system.${prefix}_${k}`, { defaultValue: k })}
          rawKey={k}
          initial={Number(v)}
          surface={surface}
          onSave={(val) => mutate(k, val)}
        />
      ))}
    </div>
  );
}

function SettingRow({
  label,
  rawKey,
  initial,
  surface,
  onSave,
}: {
  label: string;
  rawKey: string;
  initial: number;
  surface: "admin" | "webapp";
  onSave: (v: number) => void;
}) {
  return (
    <div className="webapp-row">
      <label>
        {label}
        <code className="row-hint" style={{ marginTop: 2 }}>
          {rawKey}
        </code>
      </label>
      <NumInput surface={surface} initial={initial} onSave={onSave} />
    </div>
  );
}

function NumInput({
  initial,
  surface,
  onSave,
}: {
  initial: number;
  surface: "admin" | "webapp";
  onSave: (v: number) => void;
}) {
  const [val, setVal] = useState(String(initial));
  const dirty = parseInt(val || "0") !== initial;
  const isAdmin = surface === "admin";

  if (isAdmin) {
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
            type="button"
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

  return (
    <div style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
      <input
        type="number"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        className="sa-input"
        style={{ width: "80px" }}
      />
      {dirty && (
        <button
          type="button"
          className="sa-chip active"
          onClick={() => {
            const v = parseInt(val || "0");
            if (!Number.isNaN(v)) onSave(v);
          }}
          style={{ padding: "0.25rem 0.6rem" }}
        >
          ✓
        </button>
      )}
    </div>
  );
}
