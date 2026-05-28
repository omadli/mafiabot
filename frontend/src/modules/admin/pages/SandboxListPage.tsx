import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { sandboxApi } from "@shared/api/sandbox";
import type { SandboxStatus, SandboxSummary } from "@shared/api/sandbox";

import "../components/sandbox/sandbox.css";

const STATUS_BADGE: Record<SandboxStatus, string> = {
  created: "",
  running: "yellow",
  finished: "green",
  destroyed: "",
  errored: "red",
};

function StatusBadge({ status }: { status: SandboxStatus }) {
  const { t } = useTranslation();
  const cls = STATUS_BADGE[status] || "";
  return (
    <span className={`badge ${cls}`}>
      {t(`admin.sandbox.list.status_${status}`)}
    </span>
  );
}

export function SandboxListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ["sandbox-list"],
    queryFn: () => sandboxApi.list("all", 50),
    refetchOnWindowFocus: true,
    refetchInterval: 5_000,
  });

  const destroyMutation = useMutation({
    mutationFn: (sandboxId: string) => sandboxApi.destroy(sandboxId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sandbox-list"] }),
  });

  const onDestroy = (s: SandboxSummary) => {
    if (!window.confirm(t("admin.sandbox.list.confirm_destroy"))) return;
    destroyMutation.mutate(s.sandbox_id);
  };

  return (
    <>
      <div className="sb-list-header">
        <h1 className="admin-page-title" style={{ margin: 0 }}>
          🧪 {t("admin.sandbox.title")}
        </h1>
        <button
          type="button"
          className="admin-btn primary"
          onClick={() => navigate("/admin/sandbox/new")}
        >
          + {t("admin.sandbox.list.create_button")}
        </button>
      </div>

      <div className="admin-card sb-list-table-wrap" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div className="sb-list-loading">⏳ {t("loading")}</div>
        ) : error ? (
          <div className="sb-list-loading" style={{ color: "var(--sb-err)" }}>
            ⚠️ {t("admin.sandbox.errors.list_failed")}
          </div>
        ) : !sessions || sessions.length === 0 ? (
          <div className="sb-list-empty">{t("admin.sandbox.list.empty")}</div>
        ) : (
          <table className="admin-table sb-list-table">
            <thead>
              <tr>
                <th>{t("admin.sandbox.list.col_id")}</th>
                <th>{t("admin.sandbox.list.col_status")}</th>
                <th>{t("admin.sandbox.list.col_players")}</th>
                <th>{t("admin.sandbox.list.col_mode")}</th>
                <th>{t("admin.sandbox.list.col_speed")}</th>
                <th>{t("admin.sandbox.list.col_winner")}</th>
                <th>{t("admin.sandbox.list.col_started")}</th>
                <th>{t("admin.sandbox.list.col_messages")}</th>
                <th>{t("admin.sandbox.list.col_actions")}</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.sandbox_id}>
                  <td className="sb-id-cell">
                    <Link to={`/admin/sandbox/${s.sandbox_id}`}>
                      {s.sandbox_id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td>
                    <StatusBadge status={s.status} />
                  </td>
                  <td>{s.n_players}</td>
                  <td>
                    <code style={{ fontSize: "0.85rem" }}>{s.auto_play_mode}</code>
                  </td>
                  <td>
                    <code style={{ fontSize: "0.85rem" }}>{s.timing_preset}</code>
                  </td>
                  <td>
                    {s.winner_team
                      ? t(`admin.sandbox.team_${s.winner_team}`, { defaultValue: s.winner_team })
                      : "—"}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {s.started_at
                      ? new Date(s.started_at).toLocaleString()
                      : new Date(s.created_at).toLocaleString()}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {s.transcript_summary
                      ? s.transcript_summary.n_entries.toLocaleString()
                      : "—"}
                  </td>
                  <td>
                    <div className="sb-row-actions">
                      <button
                        type="button"
                        className="admin-btn small"
                        onClick={() => navigate(`/admin/sandbox/${s.sandbox_id}`)}
                      >
                        🔍 {t("admin.sandbox.list.action_open")}
                      </button>
                      <button
                        type="button"
                        className="admin-btn small danger"
                        onClick={() => onDestroy(s)}
                        disabled={destroyMutation.isPending}
                        title={t("admin.sandbox.controls.destroy")}
                      >
                        🗑
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
