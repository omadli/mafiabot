import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import WebApp from "@twa-dev/sdk";

import { GroupSettingsPage } from "./pages/GroupSettingsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { WebAppHome } from "./pages/WebAppHome";
import { SaLayout } from "./pages/sa/SaLayout";
import { DashboardPage as SaDashboardPage } from "../sa/pages/DashboardPage";
import { RoleStatsPage as SaRolesPage } from "../sa/pages/RoleStatsPage";
import { StarsTransactionsPage } from "../sa/pages/StarsTransactionsPage";
import { RoleConfigsPage as SaRoleConfigsPage } from "../sa/pages/RoleConfigsPage";
import { EmojiConfigsPage as SaEmojiConfigsPage } from "../sa/pages/EmojiConfigsPage";
import { TopPlayersPage as SaPlayersPage } from "../sa/pages/TopPlayersPage";
import { GroupsPage as SaGroupsPage } from "../sa/pages/GroupsPage";
import { GroupDetailPage as SaGroupDetailPage } from "../sa/pages/GroupDetailPage";
import { SaLiveGamePage } from "./pages/sa/SaLiveGamePage";
import { SaSystemPage } from "./pages/sa/SaSystemPage";
import { UsersPage as SaUsersPage } from "../sa/pages/UsersPage";
import { UserDetailPage as SaUserDetailPage } from "../sa/pages/UserDetailPage";
import { GamesPage as SaGamesPage } from "../sa/pages/GamesPage";
import { GameReplayPage as SaGameReplayPage } from "../sa/pages/GameReplayPage";
import { AuditPage as SaAuditPage } from "../sa/pages/AuditPage";

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
        <Route path="history/:groupId" element={<HistoryPage />} />

        {/* SuperAdmin section — requires Telegram-ID auth (initData) */}
        <Route path="sa" element={<SaLayout />}>
          <Route index element={<SaDashboardPage />} />
          <Route path="roles" element={<SaRolesPage />} />
          <Route path="role-configs" element={<SaRoleConfigsPage />} />
          <Route path="emoji-configs" element={<SaEmojiConfigsPage />} />
          <Route path="players" element={<SaPlayersPage />} />
          <Route path="users" element={<SaUsersPage />} />
          <Route path="users/:userId" element={<SaUserDetailPage />} />
          <Route path="games" element={<SaGamesPage />} />
          <Route path="games/:gameId" element={<SaGameReplayPage />} />
          <Route path="audit" element={<SaAuditPage />} />
          <Route path="groups" element={<SaGroupsPage />} />
          <Route path="groups/:groupId" element={<SaGroupDetailPage />} />
          <Route path="groups/:groupId/live" element={<SaLiveGamePage />} />
          <Route path="system" element={<SaSystemPage />} />
          <Route path="stars" element={<StarsTransactionsPage />} />
        </Route>
      </Routes>
    </div>
  );
}
