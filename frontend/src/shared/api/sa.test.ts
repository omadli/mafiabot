import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("./client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { api } from "./client";
import { saApi } from "./sa";

describe("saApi typed wrappers", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
  });

  it("roleConfigs hits the right path", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { items: [] } });
    await saApi.roleConfigs();
    expect(api.get).toHaveBeenCalledWith("/sa/role-configs");
  });

  it("updateRoleConfig posts patch payload", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });
    await saApi.updateRoleConfig("citizen", { static_emoji: "🧑" });
    expect(api.post).toHaveBeenCalledWith(
      "/sa/role-configs/citizen",
      { static_emoji: "🧑" },
    );
  });

  it("emojiConfigs hits the right path", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { items: [] } });
    await saApi.emojiConfigs();
    expect(api.get).toHaveBeenCalledWith("/sa/emoji-configs");
  });

  it("banUser passes reason + null duration by default", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { ok: true } });
    await saApi.banUser(42, "spam");
    expect(api.post).toHaveBeenCalledWith(
      "/sa/users/42/ban",
      { reason: "spam", duration_hours: null },
    );
  });

  it("grantDiamonds defaults reason", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });
    await saApi.grantDiamonds(7, 100);
    expect(api.post).toHaveBeenCalledWith(
      "/sa/users/7/grant-diamonds",
      { amount: 100, reason: "sa grant" },
    );
  });

  it("audit forwards filter params", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { items: [], total: 0, page: 1, page_size: 30 } });
    await saApi.audit({ action: "ban", page: 2, page_size: 30 });
    expect(api.get).toHaveBeenCalledWith(
      "/sa/audit",
      { params: { action: "ban", page: 2, page_size: 30 } },
    );
  });
});
