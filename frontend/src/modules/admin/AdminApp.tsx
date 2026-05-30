import { Navigate, Route, Routes } from "react-router-dom";

import { authStore } from "@shared/store/auth";

import { AdminLayout } from "./components/AdminLayout";
import { AdminLiveGamePage } from "./pages/AdminLiveGamePage";
import { AuditPage } from "../sa/pages/AuditPage";
import { Dashboard } from "./pages/Dashboard";
import { GameReplayPage } from "./pages/GameReplayPage";
import { GamesPage } from "./pages/GamesPage";
import { EmojiConfigsPage } from "./pages/EmojiConfigsPage";
import { GroupDetailPage } from "./pages/GroupDetailPage";
import { GroupsPage } from "./pages/GroupsPage";
import { LoginPage } from "./pages/LoginPage";
import { RoleConfigsPage } from "./pages/RoleConfigsPage";
import { RoleStatsPage } from "../sa/pages/RoleStatsPage";
import { StarsTransactionsPage } from "../sa/pages/StarsTransactionsPage";
import { SandboxCreatePage } from "./pages/SandboxCreatePage";
import { SandboxDetailPage } from "./pages/SandboxDetailPage";
import { SandboxListPage } from "./pages/SandboxListPage";
import { SystemSettingsPage } from "./pages/SystemSettingsPage";
import { TopPlayersPage } from "./pages/TopPlayersPage";
import { UserDetailPage } from "./pages/UserDetailPage";
import { UsersPage } from "./pages/UsersPage";

export function AdminApp() {
  const token = authStore((s) => s.token);

  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      {token ? (
        <Route element={<AdminLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="users/:userId" element={<UserDetailPage />} />
          <Route path="groups" element={<GroupsPage />} />
          <Route path="groups/:groupId" element={<GroupDetailPage />} />
          <Route path="groups/:groupId/live" element={<AdminLiveGamePage />} />
          <Route path="games" element={<GamesPage />} />
          <Route path="games/:gameId" element={<GameReplayPage />} />
          <Route path="role-stats" element={<RoleStatsPage />} />
          <Route path="role-configs" element={<RoleConfigsPage />} />
          <Route path="emoji-configs" element={<EmojiConfigsPage />} />
          <Route path="top-players" element={<TopPlayersPage />} />
          <Route path="sandbox" element={<SandboxListPage />} />
          <Route path="sandbox/new" element={<SandboxCreatePage />} />
          <Route path="sandbox/:sandboxId" element={<SandboxDetailPage />} />
          <Route path="system-settings" element={<SystemSettingsPage />} />
          <Route path="stars-transactions" element={<StarsTransactionsPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      ) : (
        <Route path="*" element={<Navigate to="/admin/login" replace />} />
      )}
    </Routes>
  );
}
