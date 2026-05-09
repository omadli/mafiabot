import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@shared/api/client";

interface GroupItem {
  id: number;
  title: string;
  is_active: boolean;
  is_blocked: boolean;
  onboarding_completed: boolean;
  total_games: number;
  created_at: string;
}

interface GroupsResponse {
  total: number;
  page: number;
  page_size: number;
  items: GroupItem[];
}

export function GroupsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["groups", search, page],
    queryFn: async () => {
      const { data } = await api.get<GroupsResponse>("/admin/groups", {
        params: { search: search || undefined, page, page_size: 50 },
      });
      return data;
    },
  });

  const blockMutation = useMutation({
    mutationFn: async ({ groupId, reason }: { groupId: number; reason: string }) =>
      api.post(`/admin/groups/${groupId}/block`, { reason }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["groups"] }),
  });

  const unblockMutation = useMutation({
    mutationFn: async (groupId: number) => api.post(`/admin/groups/${groupId}/unblock`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["groups"] }),
  });

  return (
    <>
      <h1 className="admin-page-title">💬 Guruhlar</h1>

      <input
        className="admin-input"
        style={{ maxWidth: 500, marginBottom: "1rem" }}
        placeholder="🔍 Search by title..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />

      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nomi</th>
                <th>O'yinlar</th>
                <th>Status</th>
                <th>Yaratildi</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((g) => (
                <tr key={g.id}>
                  <td style={{ color: "var(--muted)" }}>{g.id}</td>
                  <td>{g.title}</td>
                  <td>{g.total_games}</td>
                  <td>
                    {g.is_blocked ? (
                      <span className="badge red">BLOCKED</span>
                    ) : g.onboarding_completed ? (
                      <span className="badge green">ACTIVE</span>
                    ) : (
                      <span className="badge yellow">SETUP</span>
                    )}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {new Date(g.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    {g.is_blocked ? (
                      <button
                        className="admin-btn"
                        onClick={() => unblockMutation.mutate(g.id)}
                      >
                        Unblock
                      </button>
                    ) : (
                      <button
                        className="admin-btn admin-btn-danger"
                        onClick={() => {
                          const reason = prompt("Sabab?", "Spam");
                          if (reason)
                            blockMutation.mutate({ groupId: g.id, reason });
                        }}
                      >
                        Block
                      </button>
                    )}
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
