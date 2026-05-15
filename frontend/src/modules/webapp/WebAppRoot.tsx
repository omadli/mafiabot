import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import WebApp from "@twa-dev/sdk";

import { GroupSettingsPage } from "./pages/GroupSettingsPage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { WebAppHome } from "./pages/WebAppHome";
import { SaLayout } from "./pages/sa/SaLayout";
import { SaDashboardPage } from "./pages/sa/SaDashboardPage";
import { SaRolesPage } from "./pages/sa/SaRolesPage";
import { SaPlayersPage } from "./pages/sa/SaPlayersPage";
import { SaGroupsPage } from "./pages/sa/SaGroupsPage";
import { SaGroupDetailPage } from "./pages/sa/SaGroupDetailPage";
import { SaLiveGamePage } from "./pages/sa/SaLiveGamePage";
import { SaSystemPage } from "./pages/sa/SaSystemPage";

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

        {/* SuperAdmin section — requires Telegram-ID auth (initData) */}
        <Route path="sa" element={<SaLayout />}>
          <Route index element={<SaDashboardPage />} />
          <Route path="roles" element={<SaRolesPage />} />
          <Route path="players" element={<SaPlayersPage />} />
          <Route path="groups" element={<SaGroupsPage />} />
          <Route path="groups/:groupId" element={<SaGroupDetailPage />} />
          <Route path="groups/:groupId/live" element={<SaLiveGamePage />} />
          <Route path="system" element={<SaSystemPage />} />
        </Route>
      </Routes>
    </div>
  );
}
