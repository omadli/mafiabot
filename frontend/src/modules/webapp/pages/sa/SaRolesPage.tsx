import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { saApi, type RoleConfig } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

export function SaRolesPage() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-role-stats"],
    queryFn: saApi.roleStats,
  });

  // Fetch role configs so we can show real localized name + emoji
  // (cached by the same key as the role-configs page; no extra request).
  const { data: configs } = useQuery({
    queryKey: ["sa-role-configs"],
    queryFn: saApi.roleConfigs,
    staleTime: 60_000,
  });

  const roleMap = useMemo(() => {
    const out: Record<string, RoleConfig> = {};
    (configs?.items ?? []).forEach((c) => { out[c.role] = c; });
    return out;
  }, [configs]);

  const lang = (document.documentElement.lang as "uz" | "ru" | "en") || "uz";
  const labelFor = (slug: string): string => {
    const cfg = roleMap[slug];
    if (!cfg) return `❓ ${slug}`;
    const name = lang === "ru" ? cfg.name_ru : lang === "en" ? cfg.name_en : cfg.name_uz;
    return `${cfg.static_emoji} ${name}`;
  };

  if (isLoading || !data) {
    return <div className="webapp-section">⏳ {t("loading")}</div>;
  }

  return (
    <div className="webapp-section">
      <h3>🎭 {t("roles-title")}</h3>
      <div style={{ overflowX: "auto" }}>
        <table className="sa-table">
          <thead>
            <tr>
              <th>{t("roles-col-role")}</th>
              <th style={{ textAlign: "right" }}>{t("roles-col-games")}</th>
              <th style={{ textAlign: "right" }}>{t("roles-col-wins")}</th>
              <th style={{ textAlign: "right" }}>{t("roles-col-winrate")}</th>
              <th style={{ textAlign: "right" }}>{t("roles-col-elo")}</th>
              <th style={{ textAlign: "right" }}>{t("roles-col-xp")}</th>
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
    </div>
  );
}
