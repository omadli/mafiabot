import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@shared/api/client";
import { authStore } from "@shared/store/auth";

// Re-export the shared shapes so existing imports of LivePlayer etc.
// from "../hooks/useLiveGame" continue to work; new code should import
// directly from @shared/api/liveGame.
export type {
  LiveGameState,
  LiveNightAction,
  LivePlayer,
  LiveRoundLog,
  LiveVote,
} from "@shared/api/liveGame";
import type { LiveGameState } from "@shared/api/liveGame";

/** Fetch + auto-refresh live game state via WebSocket. */
export function useLiveGame(groupId: number) {
  const qc = useQueryClient();
  const token = authStore((s) => s.token);
  const [wsConnected, setWsConnected] = useState(false);
  const [ended, setEnded] = useState(false);

  const query = useQuery({
    queryKey: ["live-game", groupId],
    queryFn: async () => {
      const { data } = await api.get<LiveGameState>(
        `/admin/groups/${groupId}/live`,
      );
      return data;
    },
    enabled: !!groupId,
    retry: false,
  });

  useEffect(() => {
    if (!token || !groupId) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${wsScheme}://${window.location.host}/ws/admin/group/${groupId}?token=${encodeURIComponent(token)}`;
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
        // Any other event invalidates the live snapshot — refetch.
        qc.invalidateQueries({ queryKey: ["live-game", groupId] });
      } catch {
        // ignore
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
