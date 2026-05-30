import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { superAdminApi, type RoleConfig } from "@shared/api/superAdmin";

import { useSa } from "../context";

/**
 * Per-role win/ELO/XP aggregates. Shared between the website's
 * `/admin/role-stats` and the WebApp's `/webapp/sa/roles` pages — the
 * only difference is the surrounding shell, which the parent layout
 * provides. The page itself is auth-agnostic: `superAdminApi.roleStats`
 * routes the call to whichever backend prefix matches the current
 * auth scheme (JWT → /admin/*, initData → /sa/*).
 */
export function RoleStatsPage() {
  const { t, i18n } = useTranslation();
  const { surface } = useSa();
  const lang = i18n.language;

  const { data, isLoading } = useQuery({
    queryKey: ["sa-role-stats"],
    queryFn: superAdminApi.roleStats,
  });

  const { data: configs } = useQuery({
    queryKey: ["sa-role-configs"],
    queryFn: superAdminApi.roleConfigs,
    staleTime: 60_000,
  });

  const roleMap = useMemo(() => {
    const out: Record<string, RoleConfig> = {};
    (configs?.items ?? []).forEach((c) => {
      out[c.role] = c;
    });
    return out;
  }, [configs]);

  const labelFor = (slug: string) => {
    const c = roleMap[slug];
    if (!c) return `❓ ${slug}`;
    const name = lang === "ru" ? c.name_ru : lang === "en" ? c.name_en : c.name_uz;
    return `${c.static_emoji} ${name}`;
  };

  // The two shells use different card/title chrome. We render the table
  // in a single shape but pick the wrapper based on the active surface.
  const titleEl =
    surface === "admin" ? (
      <h1 className="admin-page-title">📈 {t("admin.role_stats.title")}</h1>
    ) : (
      <h2 style={{ marginTop: 0 }}>📈 {t("admin.role_stats.title")}</h2>
    );

  const cardCls = surface === "admin" ? "admin-card" : "webapp-section";
  const tableCls = surface === "admin" ? "admin-table" : "sa-table";

  return (
    <>
      {titleEl}
      <div className={cardCls} style={{ padding: 0, overflow: "hidden" }}>
        {isLoading || !data ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className={tableCls}>
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
                    <td
                      style={{
                        textAlign: "right",
                        color: r.winrate_pct >= 50 ? "#4ade80" : "#e74c3c",
                      }}
                    >
                      {r.winrate_pct}%
                    </td>
                    <td
                      style={{
                        textAlign: "right",
                        color: r.avg_elo_change >= 0 ? "#4ade80" : "#e74c3c",
                      }}
                    >
                      {r.avg_elo_change >= 0 ? "+" : ""}
                      {r.avg_elo_change}
                    </td>
                    <td style={{ textAlign: "right" }}>{r.avg_xp_earned}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
