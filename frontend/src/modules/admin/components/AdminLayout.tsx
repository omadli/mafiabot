import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { LangPicker } from "@shared/components/LangPicker";
import { authStore } from "@shared/store/auth";
import type { Locale } from "@shared/i18n";

import { SaProvider } from "../../sa/context";

import "./AdminLayout.css";

interface NavItem {
  to: string;
  emoji: string;
  i18nKey: string;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/admin", emoji: "📊", i18nKey: "admin.nav.dashboard", end: true },
  { to: "/admin/users", emoji: "👥", i18nKey: "admin.nav.users" },
  { to: "/admin/groups", emoji: "💬", i18nKey: "admin.nav.groups" },
  { to: "/admin/games", emoji: "🎲", i18nKey: "admin.nav.games" },
  { to: "/admin/role-stats", emoji: "📈", i18nKey: "admin.nav.role_stats" },
  { to: "/admin/role-configs", emoji: "🎭", i18nKey: "admin.nav.role_configs" },
  { to: "/admin/emoji-configs", emoji: "✨", i18nKey: "admin.nav.emoji_configs" },
  { to: "/admin/top-players", emoji: "🏆", i18nKey: "admin.nav.top_players" },
  { to: "/admin/sandbox", emoji: "🧪", i18nKey: "admin.nav.sandbox" },
  { to: "/admin/system-settings", emoji: "⚙️", i18nKey: "admin.nav.system_settings" },
  { to: "/admin/stars-transactions", emoji: "⭐", i18nKey: "admin.nav.stars_tx" },
  { to: "/admin/audit", emoji: "📝", i18nKey: "admin.nav.audit" },
];

export function AdminLayout() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const username = authStore((s) => s.username);
  const role = authStore((s) => s.role);
  const logout = authStore((s) => s.logout);

  const onLogout = () => {
    logout();
    navigate("/admin/login");
  };

  const onLocaleChange = (code: string) => {
    i18n.changeLanguage(code as Locale);
  };

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <Link to="/admin" className="admin-logo">
          🎲 {t("admin.logo")}
        </Link>
        <nav className="admin-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `admin-nav-link ${isActive ? "active" : ""}`}
            >
              {item.emoji} {t(item.i18nKey)}
            </NavLink>
          ))}
        </nav>
        <div className="admin-user">
          <LangPicker
            value={i18n.language}
            onChange={onLocaleChange}
            className="admin-lang-select"
          />
          <div className="admin-user-name">
            {username} · <span className="role">{role}</span>
          </div>
          <button onClick={onLogout} className="admin-logout">
            🚪 {t("admin.logout")}
          </button>
        </div>
      </aside>
      <main className="admin-main">
        <SaProvider basePath="/admin" surface="admin">
          <Outlet />
        </SaProvider>
      </main>
    </div>
  );
}
