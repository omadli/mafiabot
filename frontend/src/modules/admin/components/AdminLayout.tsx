import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { authStore } from "@shared/store/auth";
import type { Locale } from "@shared/i18n";

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

  const onLocaleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    i18n.changeLanguage(e.target.value as Locale);
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
          <select
            value={i18n.language}
            onChange={onLocaleChange}
            className="admin-lang-select"
          >
            <option value="uz">🇺🇿 O&apos;zbekcha</option>
            <option value="ru">🇷🇺 Русский</option>
            <option value="en">🇬🇧 English</option>
          </select>
          <div className="admin-user-name">
            {username} · <span className="role">{role}</span>
          </div>
          <button onClick={onLogout} className="admin-logout">
            🚪 {t("admin.logout")}
          </button>
        </div>
      </aside>
      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}
