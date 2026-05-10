import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@shared/api/client";

interface UserItem {
  id: number;
  username: string | null;
  first_name: string;
  diamonds: number;
  dollars: number;
  level: number;
  is_premium: boolean;
  is_banned: boolean;
  games_total: number;
  elo: number;
}

interface UsersResponse {
  total: number;
  page: number;
  page_size: number;
  items: UserItem[];
}

export function UsersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["users", search, page],
    queryFn: async () => {
      const { data } = await api.get<UsersResponse>("/admin/users", {
        params: { search: search || undefined, page, page_size: 50 },
      });
      return data;
    },
  });

  const banMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: number; reason: string }) =>
      api.post(`/admin/users/${userId}/ban`, { reason }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const unbanMutation = useMutation({
    mutationFn: async (userId: number) => api.post(`/admin/users/${userId}/unban`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const grantMutation = useMutation({
    mutationFn: async ({ userId, amount }: { userId: number; amount: number }) =>
      api.post(`/admin/users/${userId}/grant-diamonds`, {
        amount,
        reason: "admin manual grant",
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  return (
    <>
      <h1 className="admin-page-title">👥 Foydalanuvchilar</h1>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", maxWidth: 500 }}>
        <input
          className="admin-input"
          placeholder="🔍 Search by username/name..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>💎</th>
                <th>💵</th>
                <th>Lvl</th>
                <th>ELO</th>
                <th>Games</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((u) => (
                <tr key={u.id}>
                  <td style={{ color: "var(--muted)" }}>
                    <Link to={`/admin/users/${u.id}`}>{u.id}</Link>
                  </td>
                  <td>
                    <Link to={`/admin/users/${u.id}`}>
                      <div>{u.first_name}</div>
                      <small style={{ color: "var(--muted)" }}>
                        {u.username ? `@${u.username}` : "—"}
                      </small>
                    </Link>
                  </td>
                  <td>{u.diamonds}</td>
                  <td>{u.dollars}</td>
                  <td>{u.level}</td>
                  <td>{u.elo}</td>
                  <td>{u.games_total}</td>
                  <td>
                    {u.is_premium && <span className="badge yellow">PREMIUM</span>}{" "}
                    {u.is_banned && <span className="badge red">BAN</span>}
                  </td>
                  <td style={{ display: "flex", gap: "0.4rem" }}>
                    {u.is_banned ? (
                      <button
                        className="admin-btn"
                        onClick={() => unbanMutation.mutate(u.id)}
                      >
                        Unban
                      </button>
                    ) : (
                      <button
                        className="admin-btn admin-btn-danger"
                        onClick={() => {
                          const reason = prompt("Sabab?", "Spam");
                          if (reason) banMutation.mutate({ userId: u.id, reason });
                        }}
                      >
                        Ban
                      </button>
                    )}
                    <button
                      className="admin-btn"
                      onClick={() => {
                        const amt = prompt("Olmos miqdori?", "100");
                        if (amt) grantMutation.mutate({ userId: u.id, amount: parseInt(amt) });
                      }}
                    >
                      💎+
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Pagination
        page={page}
        totalPages={Math.ceil((data?.total || 0) / 50)}
        onChange={setPage}
      />
    </>
  );
}

function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", alignItems: "center" }}>
      <button className="admin-btn" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ←
      </button>
      <span style={{ color: "var(--muted)" }}>
        Page {page} / {totalPages}
      </span>
      <button
        className="admin-btn"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        →
      </button>
    </div>
  );
}
