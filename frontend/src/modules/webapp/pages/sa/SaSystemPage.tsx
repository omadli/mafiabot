import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

const ITEM_LABELS: Record<string, string> = {
  shield: "🛡 Shield",
  killer_shield: "⛑ Killer Shield",
  vote_shield: "⚖️ Vote Shield",
  rifle: "🔫 Rifle",
  mask: "🎭 Mask",
  fake_document: "📁 Fake Document",
  special_role: "🃏 Special Role",
};

export function SaSystemPage() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-system-settings"],
    queryFn: saApi.systemSettings,
  });

  const mutation = useMutation({
    mutationFn: ({ section, key, value }: { section: any; key: string; value: any }) =>
      saApi.updateSystemSetting(section, key, value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sa-system-settings"] }),
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {t("loading")}</div>;
  }

  return (
    <>
      <h2 style={{ marginTop: 0 }}>⚙️ {t("system-title")}</h2>

      {/* Item prices */}
      <div className="webapp-section">
        <h3>{t("system-prices")}</h3>
        <table className="sa-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>💵 Dollar</th>
              <th>💎 Diamond</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.item_prices).map(([code, p]) => (
              <tr key={code}>
                <td>{ITEM_LABELS[code] ?? code}</td>
                <td>
                  <NumberInput
                    initial={p.dollars}
                    onSave={(v) =>
                      mutation.mutate({
                        section: "item_prices",
                        key: `${code}.dollars`,
                        value: v,
                      })
                    }
                  />
                </td>
                <td>
                  <NumberInput
                    initial={p.diamonds}
                    onSave={(v) =>
                      mutation.mutate({
                        section: "item_prices",
                        key: `${code}.diamonds`,
                        value: v,
                      })
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Rewards */}
      <div className="webapp-section">
        <h3>{t("system-rewards")}</h3>
        {Object.entries(data.rewards).map(([k, v]) => (
          <SettingRow
            key={k}
            label={k}
            initial={Number(v)}
            onSave={(val) => mutation.mutate({ section: "rewards", key: k, value: val })}
          />
        ))}
      </div>

      {/* Exchange */}
      <div className="webapp-section">
        <h3>{t("system-exchange")}</h3>
        {Object.entries(data.exchange).map(([k, v]) => (
          <SettingRow
            key={k}
            label={k}
            initial={typeof v === "boolean" ? (v ? 1 : 0) : Number(v)}
            onSave={(val) => mutation.mutate({ section: "exchange", key: k, value: val })}
          />
        ))}
      </div>

      {/* Premium */}
      <div className="webapp-section">
        <h3>{t("system-premium")}</h3>
        {Object.entries(data.premium).map(([k, v]) => (
          <SettingRow
            key={k}
            label={k}
            initial={Number(v)}
            onSave={(val) => mutation.mutate({ section: "premium", key: k, value: val })}
          />
        ))}
      </div>

      {data.updated_at && (
        <p style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
          🕒 {new Date(data.updated_at).toLocaleString()}
          {data.updated_by_tg_id && ` · tg_id ${data.updated_by_tg_id}`}
        </p>
      )}
    </>
  );
}

function SettingRow({
  label,
  initial,
  onSave,
}: {
  label: string;
  initial: number;
  onSave: (v: number) => void;
}) {
  return (
    <div className="webapp-row">
      <label>
        <code style={{ fontSize: "0.85rem" }}>{label}</code>
      </label>
      <NumberInput initial={initial} onSave={onSave} />
    </div>
  );
}

function NumberInput({
  initial,
  onSave,
}: {
  initial: number;
  onSave: (v: number) => void;
}) {
  const [value, setValue] = useState(String(initial));
  const dirty = parseInt(value || "0") !== initial;

  return (
    <div style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
      <input
        type="number"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="sa-input"
        style={{ width: "80px" }}
      />
      {dirty && (
        <button
          className="sa-chip active"
          onClick={() => {
            const v = parseInt(value || "0");
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
