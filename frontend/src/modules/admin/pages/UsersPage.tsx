import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
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
      <h1 className="admin-page-title">👥 {t("admin.users.title")}</h1>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", maxWidth: 500 }}>
        <input
          className="admin-input"
          placeholder={`🔍 ${t("admin.users.search_placeholder")}`}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
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
                <th>{t("admin.users.col_id")}</th>
                <th>{t("admin.users.col_name")}</th>
                <th>{t("admin.users_extra.col_diamonds")}</th>
                <th>{t("admin.users_extra.col_dollars")}</th>
                <th>{t("admin.users_extra.col_lvl")}</th>
                <th>{t("admin.users_extra.col_elo")}</th>
                <th>{t("admin.users.col_balance")}</th>
                <th>{t("admin.users.col_status")}</th>
                <th>{t("admin.users.col_actions")}</th>
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
                    {u.is_premium && (
                      <span className="badge yellow">{t("admin.users.premium")}</span>
                    )}{" "}
                    {u.is_banned && (
                      <span className="badge red">{t("admin.users.banned")}</span>
                    )}
                  </td>
                  <td style={{ display: "flex", gap: "0.4rem" }}>
                    {u.is_banned ? (
                      <button
                        className="admin-btn"
                        onClick={() => unbanMutation.mutate(u.id)}
                      >
                        {t("admin.users.unban")}
                      </button>
                    ) : (
                      <button
                        className="admin-btn admin-btn-danger"
                        onClick={() => {
                          const reason = prompt(
                            t("admin.prompts.ban_reason"),
                            t("admin.prompts.default_reason"),
                          );
                          if (reason) banMutation.mutate({ userId: u.id, reason });
                        }}
                      >
                        {t("admin.users.ban")}
                      </button>
                    )}
                    <button
                      className="admin-btn"
                      onClick={() => {
                        const amt = prompt(t("admin.users.grant_diamonds"), "100");
                        if (amt)
                          grantMutation.mutate({ userId: u.id, amount: parseInt(amt) });
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
  const { t } = useTranslation();
  if (totalPages <= 1) return null;
  return (
    <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", alignItems: "center" }}>
      <button className="admin-btn" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ←
      </button>
      <span style={{ color: "var(--muted)" }}>
        {t("admin.common.page")} {page} / {totalPages}
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
