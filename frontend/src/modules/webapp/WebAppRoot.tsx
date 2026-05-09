import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import WebApp from "@twa-dev/sdk";

import { GroupSettingsPage } from "./pages/GroupSettingsPage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { WebAppHome } from "./pages/WebAppHome";

import "./WebAppStyles.css";

export function WebAppRoot() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      WebApp.ready();
      WebApp.expand();
      // Match Telegram theme
      const colorScheme = WebApp.colorScheme;
      document.body.dataset.theme = colorScheme;
      setReady(true);
    } catch {
      // Running outside Telegram (browser)
      setReady(true);
    }
  }, []);

  if (!ready) return null;

  return (
    <div className="webapp-shell">
      <Routes>
        <Route index element={<WebAppHome />} />
        <Route path="settings/:groupId" element={<GroupSettingsPage />} />
        <Route path="leaderboard/:groupId" element={<LeaderboardPage />} />
      </Routes>
    </div>
  );
}
