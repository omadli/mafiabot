import { Navigate, Route, Routes } from "react-router-dom";

import { authStore } from "@shared/store/auth";

import { AdminLayout } from "./components/AdminLayout";
import { AuditPage } from "./pages/AuditPage";
import { Dashboard } from "./pages/Dashboard";
import { GamesPage } from "./pages/GamesPage";
import { GroupsPage } from "./pages/GroupsPage";
import { LoginPage } from "./pages/LoginPage";
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
          <Route path="groups" element={<GroupsPage />} />
          <Route path="games" element={<GamesPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      ) : (
        <Route path="*" element={<Navigate to="/admin/login" replace />} />
      )}
    </Routes>
  );
}
