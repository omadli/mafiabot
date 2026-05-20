import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

export function SaAuditPage() {
  const { t } = useTranslation();
  const { t: tFlat } = useI18n();
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-audit", action, page],
    queryFn: () => saApi.audit({ action: action || undefined, page, page_size: 30 }),
  });

  return (
    <>
      <h2 style={{ marginTop: 0 }}>📝 {t("sa.audit.title")}</h2>

      <div className="webapp-section">
        <input
          className="sa-input"
          placeholder={`🔍 ${t("sa.audit.filter_action")}`}
          value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }}
          style={{ width: "100%" }}
        />
      </div>

      {isLoading || !data ? (
        <div className="webapp-section">⏳ {tFlat("loading")}</div>
      ) : (
        <div className="webapp-section" style={{ padding: 0 }}>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {data.items.map((row) => (
              <li
                key={row.id}
                style={{
                  borderBottom: "1px solid #2a2a45",
                  padding: "0.6rem 0.9rem",
                  fontSize: 13,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong style={{ color: "var(--accent)" }}>{row.action}</strong>
                  <small style={{ color: "var(--muted)" }}>
                    {new Date(row.created_at).toLocaleString()}
                  </small>
                </div>
                {(row.target_type || row.target_id) && (
                  <div style={{ color: "var(--muted)", marginTop: 2 }}>
                    {row.target_type} · {row.target_id}
                  </div>
                )}
                {row.payload && Object.keys(row.payload).length > 0 && (
                  <details style={{ marginTop: 4 }}>
                    <summary style={{ cursor: "pointer", fontSize: 11, color: "var(--muted)" }}>
                      payload
                    </summary>
                    <pre style={{
                      margin: "4px 0 0", padding: 8, fontSize: 11,
                      background: "rgba(0,0,0,0.3)", borderRadius: 4,
                      overflow: "auto", maxHeight: 200,
                    }}>
                      {JSON.stringify(row.payload, null, 2)}
                    </pre>
                  </details>
                )}
                {(row.actor_id || row.actor_admin_id) && (
                  <small style={{ color: "var(--muted)" }}>
                    actor: {row.actor_id ? `tg #${row.actor_id}` : `admin ${row.actor_admin_id?.slice(0, 8)}`}
                  </small>
                )}
              </li>
            ))}
            {data.items.length === 0 && (
              <li style={{ padding: "1rem", textAlign: "center", color: "var(--muted)" }}>
                —
              </li>
            )}
          </ul>
          {data.total > data.page_size && (
            <div style={{
              padding: "0.6rem 0.9rem", display: "flex",
              justifyContent: "space-between", borderTop: "1px solid #2a2a45",
            }}>
              <button
                className="sa-chip"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                style={{ padding: "0.3rem 0.7rem" }}
              >
                ← {t("back")}
              </button>
              <span style={{ fontSize: 12, color: "var(--muted)" }}>
                {page} · {data.total}
              </span>
              <button
                className="sa-chip"
                disabled={page * data.page_size >= data.total}
                onClick={() => setPage(page + 1)}
                style={{ padding: "0.3rem 0.7rem" }}
              >
                →
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
