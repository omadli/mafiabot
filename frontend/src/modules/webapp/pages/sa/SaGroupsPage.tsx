import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

export function SaGroupsPage() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-groups"],
    queryFn: () => saApi.groups(1, 100),
  });

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {t("loading")}</div>;
  }

  return (
    <div className="webapp-section">
      <h3>🏘 {t("groups-title")} ({data.total})</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
          <thead>
            <tr>
              <th>{t("groups-col-id")}</th>
              <th>{t("groups-col-title")}</th>
              <th>{t("groups-col-status")}</th>
              <th style={{ textAlign: "right" }}>{t("groups-col-games")}</th>
              <th>{t("groups-col-last-game")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((g) => (
              <tr key={g.id}>
                <td style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                  <Link to={`/webapp/sa/groups/${g.id}`}>{g.id}</Link>
                </td>
                <td>
                  <Link to={`/webapp/sa/groups/${g.id}`}>{g.title}</Link>
                </td>
                <td>
                  {!g.is_active ? (
                    <span style={{ color: "var(--muted)" }}>—</span>
                  ) : g.is_blocked ? (
                    <span style={{ color: "#e74c3c" }}>🚫 {t("group-status-blocked")}</span>
                  ) : !g.onboarding_completed ? (
                    <span style={{ color: "#f0a020" }}>
                      ⏳ {t("group-status-not-onboarded")}
                    </span>
                  ) : (
                    <span style={{ color: "#4ade80" }}>✓ {t("group-status-active")}</span>
                  )}
                </td>
                <td style={{ textAlign: "right" }}>{g.games_total}</td>
                <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                  {g.last_game_at
                    ? new Date(g.last_game_at).toLocaleDateString()
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
