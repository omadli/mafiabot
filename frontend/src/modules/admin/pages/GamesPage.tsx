import { useQuery } from "@tanstack/react-query";

import { api } from "@shared/api/client";

interface GameItem {
  id: string;
  group_id: number;
  status: string;
  winner_team: string | null;
  started_at: string;
  finished_at: string | null;
  bounty_per_winner: number | null;
}

export function GamesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["games"],
    queryFn: async () =>
      (await api.get<{ items: GameItem[]; total: number }>("/admin/games")).data,
  });

  return (
    <>
      <h1 className="admin-page-title">🎲 O'yinlar</h1>
      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Group</th>
                <th>Status</th>
                <th>Winner</th>
                <th>Boshlandi</th>
                <th>Tugadi</th>
                <th>Bounty</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((g) => (
                <tr key={g.id}>
                  <td style={{ color: "var(--muted)", fontFamily: "monospace" }}>
                    {g.id.slice(0, 8)}…
                  </td>
                  <td>{g.group_id}</td>
                  <td>
                    {g.status === "finished" ? (
                      <span className="badge green">{g.status}</span>
                    ) : g.status === "running" ? (
                      <span className="badge yellow">{g.status}</span>
                    ) : (
                      <span className="badge">{g.status}</span>
                    )}
                  </td>
                  <td>{g.winner_team || "—"}</td>
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
    </>
  );
}
