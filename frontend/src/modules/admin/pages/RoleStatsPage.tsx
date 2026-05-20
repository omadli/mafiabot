import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@shared/api/admin";
import type { RoleConfig } from "@shared/api/sa";

export function RoleStatsPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const { data, isLoading } = useQuery({
    queryKey: ["admin-role-stats"],
    queryFn: adminApi.roleStats,
  });

  const { data: configs } = useQuery({
    queryKey: ["admin-role-configs"],
    queryFn: adminApi.roleConfigs,
    staleTime: 60_000,
  });

  const roleMap = useMemo(() => {
    const out: Record<string, RoleConfig> = {};
    (configs?.items ?? []).forEach((c) => { out[c.role] = c; });
    return out;
  }, [configs]);

  const labelFor = (slug: string) => {
    const c = roleMap[slug];
    if (!c) return `❓ ${slug}`;
    const name = lang === "ru" ? c.name_ru : lang === "en" ? c.name_en : c.name_uz;
    return `${c.static_emoji} ${name}`;
  };

  return (
    <>
      <h1 className="admin-page-title">📈 {t("admin.role_stats.title")}</h1>
      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading || !data ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>{t("admin.role_stats.col_role")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.role_stats.col_games")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.role_stats.col_wins")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.role_stats.col_winrate")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.role_stats.col_elo")}</th>
                <th style={{ textAlign: "right" }}>{t("admin.role_stats.col_xp")}</th>
              </tr>
            </thead>
            <tbody>
              {data.roles.map((r) => (
                <tr key={r.role}>
                  <td>{labelFor(r.role)}</td>
                  <td style={{ textAlign: "right" }}>{r.games_played}</td>
                  <td style={{ textAlign: "right" }}>{r.wins}</td>
                  <td style={{
                    textAlign: "right",
                    color: r.winrate_pct >= 50 ? "#4ade80" : "#e74c3c",
                  }}>
                    {r.winrate_pct}%
                  </td>
                  <td style={{
                    textAlign: "right",
                    color: r.avg_elo_change >= 0 ? "#4ade80" : "#e74c3c",
                  }}>
                    {r.avg_elo_change >= 0 ? "+" : ""}{r.avg_elo_change}
                  </td>
                  <td style={{ textAlign: "right" }}>{r.avg_xp_earned}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
