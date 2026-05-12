import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";

import { authStore } from "@shared/store/auth";
import { api } from "@shared/api/client";
import type { Locale } from "@shared/i18n";

export function LoginPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const setAuth = authStore((s) => s.setAuth);
  const [searchParams] = useSearchParams();
  const oneTimeToken = searchParams.get("token");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/admin/login", { username, password });
      setAuth(data.access_token, data.username, data.role);
      navigate("/admin");
    } catch (err) {
      const ax = err as AxiosError<{ detail: string }>;
      setError(ax.response?.data?.detail || t("admin.login.invalid"));
    } finally {
      setLoading(false);
    }
  };

  // Auto-login via 1-time token
  if (oneTimeToken && !authStore.getState().token) {
    api
      .post("/admin/login/one-time", { token: oneTimeToken })
      .then(({ data }) => {
        setAuth(data.access_token, data.username, data.role);
        navigate("/admin");
      })
      .catch(() => {
        setError(t("admin.login_extra.one_time_invalid"));
      });
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <select
          value={i18n.language}
          onChange={(e) => i18n.changeLanguage(e.target.value as Locale)}
          className="admin-lang-select"
          style={{ marginBottom: "1rem" }}
        >
          <option value="uz">🇺🇿 O&apos;zbekcha</option>
          <option value="ru">🇷🇺 Русский</option>
          <option value="en">🇬🇧 English</option>
        </select>
        <h1>🎲 {t("admin.logo")}</h1>
        <p className="login-sub">{t("admin.login.title")}</p>
        <form onSubmit={submit}>
          <input
            className="admin-input"
            type="text"
            placeholder={t("admin.login.username")}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
          />
          <input
            className="admin-input"
            type="password"
            placeholder={t("admin.login.password")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <div className="login-error">⚠️ {error}</div>}
          <button type="submit" className="admin-btn login-btn" disabled={loading}>
            {loading ? t("admin.login.loading") : t("admin.login.submit")}
          </button>
        </form>
        <small className="login-hint">
          {t("admin.login_extra.bot_hint")}: <code>/admin_login</code>
        </small>
      </div>
      <style>{`
        .login-shell {
          min-height: 100vh;
          display: grid;
          place-items: center;
          padding: 2rem;
        }
        .login-card {
          background: var(--card);
          padding: 2.5rem;
          border-radius: 16px;
          width: 100%;
          max-width: 400px;
        }
        .login-card h1 {
          margin: 0 0 0.5rem;
          text-align: center;
        }
        .login-sub {
          color: var(--muted);
          text-align: center;
          margin: 0 0 1.5rem;
        }
        .login-card form {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .login-error {
          color: #e74c3c;
          font-size: 0.85rem;
          padding: 0.5rem;
          background: #3d1a1a;
          border-radius: 6px;
        }
        .login-btn {
          padding: 0.75rem;
          background: var(--accent);
          border: none;
          color: white;
          font-weight: 600;
          margin-top: 0.5rem;
        }
        .login-hint {
          display: block;
          margin-top: 1.5rem;
          color: var(--muted);
          text-align: center;
          font-size: 0.8rem;
        }
        .login-hint code {
          background: #1a1a2e;
          padding: 0.1rem 0.4rem;
          border-radius: 4px;
          color: var(--accent);
        }
      `}</style>
    </div>
  );
}
