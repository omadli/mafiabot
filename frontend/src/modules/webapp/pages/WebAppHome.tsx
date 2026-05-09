import WebApp from "@twa-dev/sdk";
import { Link } from "react-router-dom";

export function WebAppHome() {
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
      <h1>📱 Mafia WebApp</h1>
      <p style={{ color: "var(--muted)" }}>
        Guruh sozlamalari va leaderboard.
      </p>
      {groupId ? (
        <div className="webapp-section">
          <Link to={`/webapp/settings/${groupId}`} className="webapp-tab active">
            ⚙️ Sozlamalar
          </Link>
          <Link
            to={`/webapp/leaderboard/${groupId}`}
            className="webapp-tab"
            style={{ marginLeft: "0.5rem" }}
          >
            🏆 Leaderboard
          </Link>
        </div>
      ) : (
        <div className="webapp-section">
          <p style={{ color: "var(--muted)" }}>
            Bu sahifa Telegram WebApp orqali ochilishi kerak. Bot guruhda
            "Sozlamalar" tugmasini bosing.
          </p>
        </div>
      )}
    </main>
  );
}
