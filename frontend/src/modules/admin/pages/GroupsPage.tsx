import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
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
      <h1 className="admin-page-title">💬 {t("admin.groups.title")}</h1>

      <input
        className="admin-input"
        style={{ maxWidth: 500, marginBottom: "1rem" }}
        placeholder={`🔍 ${t("search")}`}
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />

      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>{t("admin.groups.col_id")}</th>
                <th>{t("admin.groups.col_title")}</th>
                <th>{t("admin.groups.col_games")}</th>
                <th>{t("admin.groups.col_status")}</th>
                <th>{t("admin.users.col_joined")}</th>
                <th>{t("admin.groups.col_actions")}</th>
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
                      <span className="badge red">{t("admin.groups.blocked")}</span>
                    ) : g.onboarding_completed ? (
                      <span className="badge green">{t("admin.groups.active")}</span>
                    ) : (
                      <span className="badge yellow">
                        {t("admin.groups.not_onboarded")}
                      </span>
                    )}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {new Date(g.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                    <Link className="admin-btn" to={`/admin/groups/${g.id}/live`}>
                      🎥 {t("admin.groups.live")}
                    </Link>
                    {g.is_blocked ? (
                      <button
                        className="admin-btn"
                        onClick={() => unblockMutation.mutate(g.id)}
                      >
                        {t("admin.groups.unblock")}
                      </button>
                    ) : (
                      <button
                        className="admin-btn admin-btn-danger"
                        onClick={() => {
                          const reason = prompt(
                            t("admin.prompts.block_reason"),
                            t("admin.prompts.default_reason"),
                          );
                          if (reason)
                            blockMutation.mutate({ groupId: g.id, reason });
                        }}
                      >
                        {t("admin.groups.block")}
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
