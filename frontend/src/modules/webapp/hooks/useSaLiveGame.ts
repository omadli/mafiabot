import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { saApi } from "@shared/api/sa";

export interface LivePlayer {
  user_id: number;
  username: string | null;
  first_name: string;
  join_order: number;
  role: string;
  team: string;
  alive: boolean;
  items_active: string[];
  died_at_round: number | null;
  died_at_phase: string | null;
  died_reason: string | null;
  extra?: Record<string, unknown>;
}

export interface LiveNightAction {
  actor_id: number;
  role: string;
  action_type: string;
  target_id: number | null;
  used_item: string | null;
}

export interface LiveVote {
  voter_id: number;
  target_id: number;
  weight: number;
}

export interface LiveRoundLog {
  round_num: number;
  night_actions: LiveNightAction[];
  night_deaths: number[];
  day_votes: LiveVote[];
  hanged: number | null;
  last_words: Record<string, string>;
  extra: {
    hanging_confirm?: {
      target_id?: number;
      yes?: Record<string, number>;
      no?: Record<string, number>;
    };
    pending_hang_target?: number;
    hang_yes_total?: number;
    hang_no_total?: number;
    hang_cancelled?: boolean;
    [key: string]: unknown;
  };
}

export interface LiveGameState {
  id: string;
  group_id: number;
  chat_id: number;
  phase: string;
  round_num: number;
  phase_ends_at: number | null;
  players: LivePlayer[];
  current_actions: Record<string, LiveNightAction>;
  current_votes: Record<string, LiveVote>;
  rounds: LiveRoundLog[];
  winner_team: string | null;
  winner_user_ids: number[];
  started_at: number | null;
  finished_at: number | null;
  bounty_per_winner: number | null;
  bounty_pool: number | null;
}

function getInitData(): string {
  if (typeof window === "undefined") return "";
  const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram;
  return tg?.WebApp?.initData || "";
}

export function useSaLiveGame(groupId: number) {
  const qc = useQueryClient();
  const [wsConnected, setWsConnected] = useState(false);
  const [ended, setEnded] = useState(false);

  const query = useQuery({
    queryKey: ["sa-live-game", groupId],
    queryFn: async () => (await saApi.groupLive(groupId)) as LiveGameState,
    enabled: !!groupId,
    retry: false,
  });

  useEffect(() => {
    if (!groupId) return;
    const initData = getInitData();
    if (!initData) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${wsScheme}://${window.location.host}/ws/sa/group/${groupId}?init_data=${encodeURIComponent(initData)}`;
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
  }, [groupId, qc]);

  return { ...query, wsConnected, ended };
}
