import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

export function SaUsersPage() {
  const { t } = useTranslation();
  const { t: tFlat } = useI18n();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [banFilter, setBanFilter] = useState<boolean | undefined>(undefined);
  const [premFilter, setPremFilter] = useState<boolean | undefined>(undefined);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-users", search, page, banFilter, premFilter],
    queryFn: () =>
      saApi.users({
        search: search || undefined,
        is_banned: banFilter,
        is_premium: premFilter,
        page,
        page_size: 30,
      }),
  });

  return (
    <>
      <h2 style={{ marginTop: 0 }}>👥 {t("sa.users.title")}</h2>

      <div className="webapp-section" style={{ display: "grid", gap: "0.5rem" }}>
        <input
          className="sa-input"
          placeholder={`🔍 ${t("sa.users.search_placeholder")}`}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          <FilterChip
            label={`👑 ${t("sa.users.filter_premium")}`}
            active={premFilter === true}
            onClick={() =>
              setPremFilter((v) => (v === true ? undefined : true))
            }
          />
          <FilterChip
            label={`🚫 ${t("sa.users.filter_banned")}`}
            active={banFilter === true}
            onClick={() =>
              setBanFilter((v) => (v === true ? undefined : true))
            }
          />
        </div>
      </div>

      {isLoading || !data ? (
        <div className="webapp-section">⏳ {tFlat("loading")}</div>
      ) : (
        <div className="webapp-section" style={{ padding: 0 }}>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {data.items.map((u) => (
              <li
                key={u.id}
                style={{ borderBottom: "1px solid #2a2a45", padding: "0.6rem 0.9rem" }}
              >
                <Link
                  to={`/webapp/sa/users/${u.id}`}
                  style={{ color: "inherit", textDecoration: "none" }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "0.4rem",
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: "flex", gap: 6, alignItems: "baseline" }}>
                        <strong>{u.first_name || `#${u.id}`}</strong>
                        {u.username && (
                          <small style={{ color: "var(--muted)" }}>@{u.username}</small>
                        )}
                        {u.is_premium && <span title="premium">👑</span>}
                        {u.is_banned && <span title="banned">🚫</span>}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                        💎 {u.diamonds} · 💵 {u.dollars} · 🎮 {u.games_total} · ELO {u.elo}
                      </div>
                    </div>
                    <span style={{ color: "var(--muted)" }}>›</span>
                  </div>
                </Link>
              </li>
            ))}
            {data.items.length === 0 && (
              <li style={{ padding: "1rem", textAlign: "center", color: "var(--muted)" }}>
                {t("sa.users.empty")}
              </li>
            )}
          </ul>
          <Pager total={data.total} page={data.page} pageSize={data.page_size} onPage={setPage} />
        </div>
      )}
    </>
  );
}

function FilterChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      className={`sa-chip ${active ? "active" : ""}`}
      onClick={onClick}
      style={{ padding: "0.3rem 0.7rem" }}
    >
      {label}
    </button>
  );
}

function Pager({
  total, page, pageSize, onPage,
}: { total: number; page: number; pageSize: number; onPage: (p: number) => void }) {
  const { t } = useTranslation();
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <div style={{
      padding: "0.6rem 0.9rem",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      gap: "0.4rem",
      borderTop: "1px solid #2a2a45",
    }}>
      <button
        className="sa-chip"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
        style={{ padding: "0.3rem 0.7rem" }}
      >
        ← {t("back")}
      </button>
      <span style={{ fontSize: 12, color: "var(--muted)" }}>
        {page} / {pages} · {total}
      </span>
      <button
        className="sa-chip"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
        style={{ padding: "0.3rem 0.7rem" }}
      >
        →
      </button>
    </div>
  );
}
