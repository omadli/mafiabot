import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { authStore } from "@shared/store/auth";

import "./AdminLayout.css";

const NAV_ITEMS = [
  { to: "/admin", label: "📊 Dashboard", end: true },
  { to: "/admin/users", label: "👥 Foydalanuvchilar" },
  { to: "/admin/groups", label: "💬 Guruhlar" },
  { to: "/admin/games", label: "🎲 O'yinlar" },
  { to: "/admin/audit", label: "📝 Audit Log" },
];

export function AdminLayout() {
  const navigate = useNavigate();
  const username = authStore((s) => s.username);
  const role = authStore((s) => s.role);
  const logout = authStore((s) => s.logout);

  const onLogout = () => {
    logout();
    navigate("/admin/login");
  };

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <Link to="/admin" className="admin-logo">
          🎲 Mafia Admin
        </Link>
        <nav className="admin-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `admin-nav-link ${isActive ? "active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="admin-user">
          <div className="admin-user-name">
            {username} · <span className="role">{role}</span>
          </div>
          <button onClick={onLogout} className="admin-logout">
            🚪 Chiqish
          </button>
        </div>
      </aside>
      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}
