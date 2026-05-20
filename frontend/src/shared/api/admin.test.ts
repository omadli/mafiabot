import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("./client", () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

import { api } from "./client";
import { adminApi } from "./admin";

describe("adminApi typed wrappers (JWT auth path)", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
  });

  it("roleConfigs hits /admin/role-configs (not /sa/)", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { items: [] } });
    await adminApi.roleConfigs();
    expect(api.get).toHaveBeenCalledWith("/admin/role-configs");
  });

  it("emojiConfigs hits /admin/emoji-configs", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { items: [] } });
    await adminApi.emojiConfigs();
    expect(api.get).toHaveBeenCalledWith("/admin/emoji-configs");
  });

  it("updateRoleConfig posts to admin namespace", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });
    await adminApi.updateRoleConfig("doctor", { name_uz: "Doktor" });
    expect(api.post).toHaveBeenCalledWith(
      "/admin/role-configs/doctor",
      { name_uz: "Doktor" },
    );
  });

  it("systemSettings hits admin namespace", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { item_prices: {}, rewards: {}, exchange: {}, premium: {}, updated_at: null, updated_by_tg_id: null },
    });
    await adminApi.systemSettings();
    expect(api.get).toHaveBeenCalledWith("/admin/system-settings");
  });

  it("groupGames passes pagination params", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { group_id: 1, total: 0, page: 1, items: [] } });
    await adminApi.groupGames(123, 2, 25);
    expect(api.get).toHaveBeenCalledWith(
      "/admin/groups/123/games",
      { params: { page: 2, page_size: 25 } },
    );
  });
});
