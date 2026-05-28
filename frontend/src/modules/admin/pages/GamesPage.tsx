import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";
import { Pagination, SortableHeader, useTableState } from "@shared/components/TableTools";

interface GameItem {
  id: string;
  group_id: number;
  status: string;
  winner_team: string | null;
  started_at: string;
  finished_at: string | null;
  bounty_per_winner: number | null;
}

interface GamesResponse {
  items: GameItem[];
  total: number;
  page: number;
  page_size: number;
}

const PAGE_SIZE = 50;

export function GamesPage() {
  const { t } = useTranslation();
  const { page, setPage, sort, setSort } = useTableState({
    initialSort: { by: "started_at", dir: "desc" },
  });
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [groupFilter, setGroupFilter] = useState<string>("");

  const { data, isLoading } = useQuery({
    queryKey: ["games", page, sort, statusFilter, groupFilter],
    queryFn: async () => {
      const { data } = await api.get<GamesResponse>("/admin/games", {
        params: {
          page,
          page_size: PAGE_SIZE,
          sort_by: sort?.by,
          sort_dir: sort?.dir,
          status: statusFilter || undefined,
          group_id: groupFilter || undefined,
        },
      });
      return data;
    },
  });

  return (
    <>
      <h1 className="admin-page-title">🎲 {t("admin.games.title")}</h1>

      <div
        style={{
          display: "flex",
          gap: "0.6rem",
          marginBottom: "1rem",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <select
          className="admin-input"
          style={{ width: "auto" }}
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">{t("admin.games.filter_all", "All statuses")}</option>
          <option value="running">{t("admin.games.status_running", "Running")}</option>
          <option value="finished">{t("admin.games.status_finished", "Finished")}</option>
          <option value="cancelled">{t("admin.games.status_cancelled", "Cancelled")}</option>
        </select>
        <input
          className="admin-input"
          style={{ width: 160 }}
          placeholder={t("admin.games.filter_group", "Group ID")}
          value={groupFilter}
          onChange={(e) => {
            setGroupFilter(e.target.value.replace(/[^0-9-]/g, ""));
            setPage(1);
          }}
        />
      </div>

      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>{t("admin.games.col_id")}</th>
                <th>{t("admin.games.col_group")}</th>
                <th>{t("admin.games.col_status")}</th>
                <th>{t("admin.games.col_winner")}</th>
                <SortableHeader field="started_at" sort={sort} onChange={setSort}>
                  {t("admin.games.col_started")}
                </SortableHeader>
                <SortableHeader field="finished_at" sort={sort} onChange={setSort}>
                  {t("admin.games.col_duration")}
                </SortableHeader>
                <th>{t("admin.games_extra.col_bounty")}</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((g) => (
                <tr key={g.id}>
                  <td style={{ color: "var(--muted)", fontFamily: "monospace" }}>
                    <Link to={`/admin/games/${g.id}`}>{g.id.slice(0, 8)}…</Link>
                  </td>
                  <td>
                    <Link to={`/admin/groups/${g.group_id}/live`}>{g.group_id}</Link>
                  </td>
                  <td>
                    {g.status === "finished" ? (
                      <span className="badge green">{t(`admin.games.status_${g.status}`)}</span>
                    ) : g.status === "running" ? (
                      <span className="badge yellow">{t(`admin.games.status_${g.status}`)}</span>
                    ) : (
                      <span className="badge">{t(`admin.games.status_${g.status}`, g.status)}</span>
                    )}
                  </td>
                  <td>
                    {g.winner_team ? t(`admin.games.team_${g.winner_team}`, g.winner_team) : "—"}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {new Date(g.started_at).toLocaleString()}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {g.finished_at ? new Date(g.finished_at).toLocaleString() : "—"}
                  </td>
                  <td>{g.bounty_per_winner ? `💎 ${g.bounty_per_winner}` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Pagination
        page={page}
        totalPages={Math.ceil((data?.total || 0) / PAGE_SIZE)}
        onChange={setPage}
        total={data?.total}
        pageSize={PAGE_SIZE}
      />
    </>
  );
}
