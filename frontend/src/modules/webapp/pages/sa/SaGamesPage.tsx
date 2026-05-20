import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { saApi } from "@shared/api/sa";
import { useI18n } from "@shared/i18n/useI18n";

const STATUS_OPTIONS: { key: string; label_key: string }[] = [
  { key: "",          label_key: "sa.games.filter_all" },
  { key: "finished",  label_key: "sa.games.filter_finished" },
  { key: "running",   label_key: "sa.games.filter_running" },
  { key: "waiting",   label_key: "sa.games.filter_waiting" },
  { key: "cancelled", label_key: "sa.games.filter_cancelled" },
];

export function SaGamesPage() {
  const { t } = useTranslation();
  const { t: tFlat } = useI18n();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["sa-games", status, page],
    queryFn: () => saApi.games({ status: status || undefined, page, page_size: 30 }),
  });

  return (
    <>
      <h2 style={{ marginTop: 0 }}>🎲 {t("sa.games.title")}</h2>

      <div className="webapp-section">
        <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              className={`sa-chip ${status === opt.key ? "active" : ""}`}
              onClick={() => { setStatus(opt.key); setPage(1); }}
              style={{ padding: "0.3rem 0.7rem", fontSize: 12 }}
            >
              {t(opt.label_key)}
            </button>
          ))}
        </div>
      </div>

      {isLoading || !data ? (
        <div className="webapp-section">⏳ {tFlat("loading")}</div>
      ) : (
        <div className="webapp-section" style={{ padding: 0 }}>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {data.items.map((g) => (
              <li
                key={g.id}
                style={{ borderBottom: "1px solid #2a2a45", padding: "0.6rem 0.9rem" }}
              >
                <Link
                  to={`/webapp/sa/games/${g.id}`}
                  style={{ color: "inherit", textDecoration: "none" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <strong style={{ fontSize: 13 }}>
                      <code>{g.id.slice(0, 8)}</code>
                    </strong>
                    <StatusBadge status={g.status} />
                  </div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                    grp #{g.group_id} ·{" "}
                    {g.winner_team
                      ? `🏆 ${t(`sa.games.winner_${g.winner_team}`, { defaultValue: g.winner_team })}`
                      : "—"}{" "}
                    {g.bounty_per_winner ? ` · 💎${g.bounty_per_winner}` : ""}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>
                    {g.started_at && new Date(g.started_at).toLocaleString()}
                  </div>
                </Link>
              </li>
            ))}
            {data.items.length === 0 && (
              <li style={{ padding: "1rem", textAlign: "center", color: "var(--muted)" }}>
                —
              </li>
            )}
          </ul>
          {data.total > data.page_size && (
            <div style={{
              padding: "0.6rem 0.9rem", display: "flex",
              justifyContent: "space-between", borderTop: "1px solid #2a2a45",
            }}>
              <button
                className="sa-chip"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                style={{ padding: "0.3rem 0.7rem" }}
              >
                ← {t("back")}
              </button>
              <span style={{ fontSize: 12, color: "var(--muted)" }}>
                {page} · {data.total}
              </span>
              <button
                className="sa-chip"
                disabled={page * data.page_size >= data.total}
                onClick={() => setPage(page + 1)}
                style={{ padding: "0.3rem 0.7rem" }}
              >
                →
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}

function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const color: Record<string, string> = {
    finished: "#4ade80",
    running:  "#f0a020",
    waiting:  "#8a90a0",
    cancelled: "#e74c3c",
  };
  return (
    <span style={{
      fontSize: 11, padding: "2px 8px", borderRadius: 999,
      background: "rgba(255,255,255,0.06)", color: color[status] || "var(--muted)",
    }}>
      {t(`sa.games.status_${status}`, { defaultValue: status })}
    </span>
  );
}
