import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";
import { Pagination, SortableHeader, useTableState } from "@shared/components/TableTools";
import { TgGroup } from "@shared/components/TgLink";

interface GroupItem {
  id: number;
  title: string;
  invite_link: string | null;
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
  const { search, setSearch, page, setPage, sort, setSort } = useTableState({
    initialSort: { by: "id", dir: "desc" },
  });
  const [isBlocked, setIsBlocked] = useState<boolean | "">("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["groups", search, page, sort, isBlocked],
    queryFn: async () => {
      const { data } = await api.get<GroupsResponse>("/admin/groups", {
        params: {
          search: search || undefined,
          page,
          page_size: 50,
          sort_by: sort?.by,
          sort_dir: sort?.dir,
          is_blocked: isBlocked === "" ? undefined : isBlocked,
        },
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
          placeholder={`🔍 ${t("search")}`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="admin-input"
          style={{ width: "auto" }}
          value={isBlocked === "" ? "" : isBlocked ? "y" : "n"}
          onChange={(e) => {
            const v = e.target.value;
            setIsBlocked(v === "" ? "" : v === "y");
            setPage(1);
          }}
        >
          <option value="">{t("admin.groups.filter_all", "All")}</option>
          <option value="y">{t("admin.groups.blocked")}</option>
          <option value="n">{t("admin.groups.filter_active", "Not blocked")}</option>
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
                  {t("admin.groups.col_id")}
                </SortableHeader>
                <SortableHeader field="title" sort={sort} onChange={setSort} initialDir="asc">
                  {t("admin.groups.col_title")}
                </SortableHeader>
                <th>{t("admin.groups.col_games")}</th>
                <th>{t("admin.groups.col_status")}</th>
                <SortableHeader field="created_at" sort={sort} onChange={setSort}>
                  {t("admin.users.col_joined")}
                </SortableHeader>
                <th>{t("admin.groups.col_actions")}</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((g) => (
                <tr key={g.id}>
                  <td style={{ color: "var(--muted)" }}>{g.id}</td>
                  <td>
                    <TgGroup
                      title={g.title}
                      inviteLink={g.invite_link}
                      internalHref={`/admin/groups/${g.id}/live`}
                      showInvite
                    />
                  </td>
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
