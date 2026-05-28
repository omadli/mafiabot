import { Link, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";
import { LangPicker } from "@shared/components/LangPicker";
import { useI18n } from "@shared/i18n/useI18n";

const NAV = [
  { path: "/webapp/sa", label: "📊", labelKey: "sa-nav-dashboard" },
  { path: "/webapp/sa/users", label: "👥", labelKey: "sa-nav-users" },
  { path: "/webapp/sa/groups", label: "🏘", labelKey: "sa-nav-groups" },
  { path: "/webapp/sa/games", label: "🎲", labelKey: "sa-nav-games" },
  { path: "/webapp/sa/roles", label: "📈", labelKey: "sa-nav-roles" },
  { path: "/webapp/sa/role-configs", label: "🎭", labelKey: "sa-nav-role-configs" },
  { path: "/webapp/sa/emoji-configs", label: "✨", labelKey: "sa-nav-emoji-configs" },
  { path: "/webapp/sa/players", label: "🏆", labelKey: "sa-nav-players" },
  { path: "/webapp/sa/system", label: "⚙️", labelKey: "sa-nav-system" },
  { path: "/webapp/sa/audit", label: "📝", labelKey: "sa-nav-audit" },
];

export function SaLayout() {
  const { t, setLocale, locale } = useI18n();
  const { pathname } = useLocation();

  const { data: me, isLoading, error } = useQuery({
    queryKey: ["sa-me"],
    queryFn: saApi.me,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="webapp-section">
        <p>⏳ {t("loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="webapp-section">
        <h3>🚫 {t("sa-access-denied")}</h3>
        <p style={{ color: "var(--muted)" }}>{t("sa-access-denied-hint")}</p>
      </div>
    );
  }

  return (
    <div className="sa-shell">
      <header className="sa-header">
        <div>
          <strong>🛡 SuperAdmin</strong>
          <small style={{ color: "var(--muted)", marginLeft: 8 }}>
            {me?.first_name}
          </small>
        </div>
        <LangPicker
          value={locale}
          onChange={(code) => setLocale(code as "uz" | "ru" | "en")}
          className="sa-lang-select"
          iconOnly
        />
      </header>

      <nav className="sa-nav">
        {NAV.map((item) => {
          const active =
            item.path === "/webapp/sa"
              ? pathname === "/webapp/sa" || pathname === "/webapp/sa/"
              : pathname.startsWith(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sa-nav-btn ${active ? "active" : ""}`}
            >
              <span>{item.label}</span>
              <small>{t(item.labelKey)}</small>
            </Link>
          );
        })}
      </nav>

      <main className="sa-content">
        <Outlet />
      </main>
    </div>
  );
}
