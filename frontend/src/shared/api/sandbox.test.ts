/**
 * Smoke tests for sandboxApi — verifies each method hits the right URL +
 * payload shape. Catches accidental route renames before they reach QA.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./client", () => ({
  api: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

import { api } from "./client";
import { sandboxApi } from "./sandbox";

const SID = "11111111-2222-3333-4444-555555555555";

describe("sandboxApi (JWT super-admin)", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
    vi.mocked(api.delete).mockReset();
  });

  it("create posts to /sa/sandbox/games with the request body", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { sandbox_id: SID } });
    await sandboxApi.create({ n_players: 8, mafia_ratio: "low" });
    expect(api.post).toHaveBeenCalledWith("/sa/sandbox/games", {
      n_players: 8,
      mafia_ratio: "low",
    });
  });

  it("list defaults to status=all + limit=50", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] });
    await sandboxApi.list();
    expect(api.get).toHaveBeenCalledWith("/sa/sandbox/games", {
      params: { status: "all", limit: 50 },
    });
  });

  it("list with status=active passes through", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] });
    await sandboxApi.list("active", 10);
    expect(api.get).toHaveBeenCalledWith("/sa/sandbox/games", {
      params: { status: "active", limit: 10 },
    });
  });

  it("get hits /sa/sandbox/games/{id}", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: {} });
    await sandboxApi.get(SID);
    expect(api.get).toHaveBeenCalledWith(`/sa/sandbox/games/${SID}`);
  });

  it("start/stop/restart/advance all POST to the right subpath", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} });
    await sandboxApi.start(SID);
    await sandboxApi.stop(SID);
    await sandboxApi.restart(SID);
    await sandboxApi.advance(SID);
    expect(api.post).toHaveBeenNthCalledWith(1, `/sa/sandbox/games/${SID}/start`);
    expect(api.post).toHaveBeenNthCalledWith(2, `/sa/sandbox/games/${SID}/stop`);
    expect(api.post).toHaveBeenNthCalledWith(3, `/sa/sandbox/games/${SID}/restart`);
    expect(api.post).toHaveBeenNthCalledWith(4, `/sa/sandbox/games/${SID}/advance`);
  });

  it("destroy DELETEs the game row", async () => {
    vi.mocked(api.delete).mockResolvedValueOnce({ data: { ok: true } });
    await sandboxApi.destroy(SID);
    expect(api.delete).toHaveBeenCalledWith(`/sa/sandbox/games/${SID}`);
  });

  it("callback POSTs the click payload", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { ok: true } });
    await sandboxApi.callback(SID, {
      user_id: -123,
      callback_data: "night:doctor:42",
      message_id: 17,
    });
    expect(api.post).toHaveBeenCalledWith(
      `/sa/sandbox/games/${SID}/callback`,
      { user_id: -123, callback_data: "night:doctor:42", message_id: 17 },
    );
  });

  it("state GETs the live snapshot endpoint", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: {} });
    await sandboxApi.state(SID);
    expect(api.get).toHaveBeenCalledWith(`/sa/sandbox/games/${SID}/state`);
  });

  it("transcript GETs with pagination params", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { entries: [], next_since: 0 },
    });
    await sandboxApi.transcript(SID, 42, 100);
    expect(api.get).toHaveBeenCalledWith(`/sa/sandbox/games/${SID}/transcript`, {
      params: { since: 42, limit: 100 },
    });
  });

  it("transcript defaults: since=0, limit=200", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { entries: [], next_since: 0 },
    });
    await sandboxApi.transcript(SID);
    expect(api.get).toHaveBeenCalledWith(`/sa/sandbox/games/${SID}/transcript`, {
      params: { since: 0, limit: 200 },
    });
  });
});
