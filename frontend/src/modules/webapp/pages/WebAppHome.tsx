import WebApp from "@twa-dev/sdk";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function WebAppHome() {
  const { t } = useTranslation();

  let groupId: number | null = null;
  let startParam: string | undefined;
  try {
    startParam = WebApp.initDataUnsafe?.start_param;
    if (startParam?.startsWith("settings_")) {
      groupId = parseInt(startParam.replace("settings_", ""));
    }
  } catch {
    // not in Telegram context
  }

  return (
    <main>
      <h1>{t("webapp_home.title")}</h1>
      <p style={{ color: "var(--muted)" }}>{t("webapp_home.subtitle")}</p>
      {groupId ? (
        <div className="webapp-section">
          <Link to={`/webapp/settings/${groupId}`} className="webapp-tab active">
            {t("webapp_home.settings_btn")}
          </Link>
          <Link
            to={`/webapp/leaderboard/${groupId}`}
            className="webapp-tab"
            style={{ marginLeft: "0.5rem" }}
          >
            {t("webapp_home.leaderboard_btn")}
          </Link>
        </div>
      ) : (
        <div className="webapp-section">
          <p style={{ color: "var(--muted)" }}>{t("webapp_home.open_via_telegram")}</p>
        </div>
      )}
    </main>
  );
}
