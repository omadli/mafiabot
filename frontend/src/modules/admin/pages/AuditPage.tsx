import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";

interface AuditItem {
  id: string;
  actor_id: number | null;
  actor_admin_id: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  payload: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export function AuditPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: async () =>
      (await api.get<{ items: AuditItem[]; total: number }>("/admin/audit")).data,
    refetchInterval: 10_000,
  });

  return (
    <>
      <h1 className="admin-page-title">📝 {t("admin.audit.title")}</h1>
      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>{t("admin.audit.col_time")}</th>
                <th>{t("admin.audit.col_actor")}</th>
                <th>{t("admin.audit.col_action")}</th>
                <th>{t("admin.audit.col_target")}</th>
                <th>{t("admin.audit.col_payload")}</th>
                <th>{t("admin.audit.col_ip")}</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((log) => (
                <tr key={log.id}>
                  <td style={{ color: "var(--muted)", whiteSpace: "nowrap" }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td>
                    {log.actor_admin_id
                      ? `admin:${log.actor_admin_id.slice(0, 8)}…`
                      : log.actor_id
                        ? `user:${log.actor_id}`
                        : "system"}
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                    {log.action}
                  </td>
                  <td>
                    {log.target_type ? `${log.target_type}:${log.target_id}` : "—"}
                  </td>
                  <td
                    style={{
                      fontFamily: "monospace",
                      fontSize: "0.75rem",
                      color: "var(--muted)",
                      maxWidth: 280,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {Object.keys(log.payload || {}).length > 0
                      ? JSON.stringify(log.payload)
                      : "—"}
                  </td>
                  <td style={{ color: "var(--muted)" }}>{log.ip_address || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
