import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";
import { Pagination, SortableHeader, useTableState } from "@shared/components/TableTools";
import { TgUser } from "@shared/components/TgLink";

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
  const { search, setSearch, page, setPage, sort, setSort } = useTableState({
    initialSort: { by: "id", dir: "desc" },
  });
  const [isBanned, setIsBanned] = useState<boolean | "">("");
  const [isPremium, setIsPremium] = useState<boolean | "">("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["users", search, page, sort, isBanned, isPremium],
    queryFn: async () => {
      const { data } = await api.get<UsersResponse>("/admin/users", {
        params: {
          search: search || undefined,
          page,
          page_size: 50,
          sort_by: sort?.by,
          sort_dir: sort?.dir,
          is_banned: isBanned === "" ? undefined : isBanned,
          is_premium: isPremium === "" ? undefined : isPremium,
        },
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

      <div
        style={{
          display: "flex",
          gap: "0.6rem",
          marginBottom: "1rem",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <input
          className="admin-input"
          style={{ flex: "1 1 260px", maxWidth: 360 }}
          placeholder={`🔍 ${t("admin.users.search_placeholder")}`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="admin-input"
          style={{ width: "auto" }}
          value={isBanned === "" ? "" : isBanned ? "y" : "n"}
          onChange={(e) => {
            const v = e.target.value;
            setIsBanned(v === "" ? "" : v === "y");
            setPage(1);
          }}
        >
          <option value="">{t("admin.users.filter_ban_all", "All")}</option>
          <option value="y">{t("admin.users.banned")}</option>
          <option value="n">{t("admin.users.filter_not_banned", "Not banned")}</option>
        </select>
        <select
          className="admin-input"
          style={{ width: "auto" }}
          value={isPremium === "" ? "" : isPremium ? "y" : "n"}
          onChange={(e) => {
            const v = e.target.value;
            setIsPremium(v === "" ? "" : v === "y");
            setPage(1);
          }}
        >
          <option value="">{t("admin.users.filter_premium_all", "All")}</option>
          <option value="y">{t("admin.users.premium")}</option>
          <option value="n">{t("admin.users.filter_not_premium", "Not premium")}</option>
        </select>
      </div>

      <div className="admin-card" style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: "2rem", textAlign: "center" }}>⏳ {t("loading")}</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <SortableHeader field="id" sort={sort} onChange={setSort}>
                  {t("admin.users.col_id")}
                </SortableHeader>
                <th>{t("admin.users.col_name")}</th>
                <SortableHeader field="diamonds" sort={sort} onChange={setSort}>
                  {t("admin.users_extra.col_diamonds")}
                </SortableHeader>
                <SortableHeader field="dollars" sort={sort} onChange={setSort}>
                  {t("admin.users_extra.col_dollars")}
                </SortableHeader>
                <SortableHeader field="level" sort={sort} onChange={setSort}>
                  {t("admin.users_extra.col_lvl")}
                </SortableHeader>
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
                    <TgUser
                      id={u.id}
                      firstName={u.first_name}
                      username={u.username}
                      internalHref={`/admin/users/${u.id}`}
                    />
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
        total={data?.total}
        pageSize={50}
      />
    </>
  );
}
