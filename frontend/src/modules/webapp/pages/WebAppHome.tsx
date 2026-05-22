import { useEffect, useMemo } from "react";
import WebApp from "@twa-dev/sdk";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

/**
 * Parses Telegram's `start_param` (e.g. `settings_<id>`, `history_<id>`,
 * `leaderboard_<id>`), and if it points to a sub-page, navigates there
 * directly. Falls back to a manual nav grid when opened without a
 * recognised payload (e.g. browser preview, or bot opened the WebApp
 * with no params).
 */
const ROUTABLE_PREFIXES: Record<string, string> = {
  settings_: "settings",
  history_: "history",
  leaderboard_: "leaderboard",
};

interface ParsedStart {
  groupId: number | null;
  route: string | null;
}

function parseStartParam(): ParsedStart {
  // Telegram surfaces the start param two different ways:
  //   1. `tg.initDataUnsafe.start_param` — populated when the WebApp is
  //      launched via "Direct Link Mini App" (t.me link with ?startapp=...).
  //   2. Plain `?start=…` query string on the URL — populated when an
  //      inline KeyboardButton/web_app button hands the user a URL that
  //      embeds the routing hint. aiogram does NOT pipe start_param into
  //      Telegram for inline WebApp buttons, so this is our actual path
  //      from the /settings DM menu.
  let startParam: string | undefined;
  try {
    startParam = WebApp.initDataUnsafe?.start_param;
  } catch {
    // ignore — we'll fall back to the URL query
  }
  if (!startParam && typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    startParam =
      params.get("start") ||
      params.get("tgWebAppStartParam") ||
      undefined;
  }
  if (!startParam) return { groupId: null, route: null };
  for (const [prefix, route] of Object.entries(ROUTABLE_PREFIXES)) {
    if (startParam.startsWith(prefix)) {
      const parsed = parseInt(startParam.slice(prefix.length));
      if (!Number.isNaN(parsed)) return { groupId: parsed, route };
    }
  }
  return { groupId: null, route: null };
}

export function WebAppHome() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Parse once per mount — `start_param` is set by Telegram and doesn't
  // change while the WebApp is open.
  const { groupId, route } = useMemo(parseStartParam, []);

  // Auto-redirect when the user came in via a specific bot menu button
  // (settings / history / leaderboard). The nav grid only makes sense
  // when the WebApp was opened without a route hint.
  useEffect(() => {
    if (groupId !== null && route) {
      navigate(`/webapp/${route}/${groupId}`, { replace: true });
    }
  }, [groupId, route, navigate]);

  return (
    <main>
      <h1>{t("webapp_home.title")}</h1>
      <p style={{ color: "var(--muted)" }}>{t("webapp_home.subtitle")}</p>
      {groupId !== null ? (
        <div className="webapp-section webapp-home-nav">
          <Link to={`/webapp/settings/${groupId}`} className="webapp-tab active">
            {t("webapp_home.settings_btn")}
          </Link>
          <Link to={`/webapp/leaderboard/${groupId}`} className="webapp-tab">
            {t("webapp_home.leaderboard_btn")}
          </Link>
          <Link to={`/webapp/history/${groupId}`} className="webapp-tab">
            {t("webapp_home.history_btn")}
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
