import { useQuery } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

const ROLE_EMOJI: Record<string, string> = {
  citizen: "👨🏼",
  detective: "🕵🏻‍♂",
  sergeant: "👮🏻‍♂",
  mayor: "🎖",
  doctor: "👨🏻‍⚕",
  hooker: "💃",
  hobo: "🧙‍♂",
  lucky: "🤞🏼",
  suicide: "🤦🏼",
  kamikaze: "💣",
  don: "🤵🏻",
  mafia: "🤵🏼",
  lawyer: "👨‍💼",
  journalist: "👩🏼‍💻",
  killer: "🥷",
  maniac: "🔪",
  werewolf: "🐺",
  mage: "🧙",
  arsonist: "🧟",
  crook: "🤹",
  snitch: "🤓",
};

export function SaRolesPage() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["sa-role-stats"],
    queryFn: saApi.roleStats,
  });

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
                <td>
                  {ROLE_EMOJI[r.role] ?? "❓"} {r.role}
                </td>
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
