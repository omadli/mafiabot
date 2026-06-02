/**
 * Surface-agnostic live game state + WebSocket subscription.
 *
 * Both shells of the SuperAdmin UI watch the same `LiveGameState`
 * shape, but they authenticate differently:
 *
 *   admin (website)  — JWT in Authorization header + ?token=... on the
 *                      WebSocket → /ws/admin/group/:id
 *   webapp (Mini App) — Telegram initData on the WebSocket query string
 *                      → /ws/sa/group/:id
 *
 * The HTTP fetch routes through `superAdminApi.groupLive`, which
 * already does the dispatch (JWT → `/admin/*`, initData → `/sa/*`).
 * Only the WebSocket URL needs the same fork. Auth presence in the
 * Zustand store is the discriminator — if a JWT is set, we open the
 * admin WS; otherwise we use initData. Same React hook surface
 * either way.
 */

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { superAdminApi } from "@shared/api/superAdmin";
import type { LiveGameState } from "@shared/api/liveGame";
import { authStore } from "@shared/store/auth";

function getInitData(): string {
  if (typeof window === "undefined") return "";
  const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram;
  return tg?.WebApp?.initData || "";
}

export function useLiveGame(groupId: number) {
  const qc = useQueryClient();
  const token = authStore((s) => s.token);
  const [wsConnected, setWsConnected] = useState(false);
  const [ended, setEnded] = useState(false);

  const query = useQuery({
    queryKey: ["sa-live-game", groupId],
    queryFn: async () =>
      (await superAdminApi.groupLive(groupId)) as LiveGameState,
    enabled: !!groupId,
    retry: false,
  });

  useEffect(() => {
    if (!groupId) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";

    // Pick WS endpoint based on which credential we have. JWT in
    // the auth store ⇒ admin shell; otherwise assume initData.
    let url: string;
    if (token) {
      url = `${wsScheme}://${window.location.host}/ws/admin/group/${groupId}?token=${encodeURIComponent(token)}`;
    } else {
      const initData = getInitData();
      if (!initData) return;
      url = `${wsScheme}://${window.location.host}/ws/sa/group/${groupId}?init_data=${encodeURIComponent(initData)}`;
    }

    const ws = new WebSocket(url);

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data);
        if (evt.type === "game_cleared") {
          setEnded(true);
          return;
        }
        qc.invalidateQueries({ queryKey: ["sa-live-game", groupId] });
      } catch {
        // ignore malformed events
      }
    };

    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 30_000);

    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [token, groupId, qc]);

  return { ...query, wsConnected, ended };
}

export type { LiveGameState };
