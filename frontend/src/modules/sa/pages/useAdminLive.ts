/**
 * Admin live event stream (WebSocket).
 *
 * Same wire format as the JWT-protected /ws/admin endpoint. The hook is
 * imported by the unified DashboardPage; the WebApp shell passes
 * `enabled=false` because it has no persisted JWT to authenticate the
 * WebSocket with — Telegram WebApps authenticate per-request via
 * initData and the WS endpoint doesn't accept that yet.
 */

import { useEffect, useState } from "react";

import { authStore } from "@shared/store/auth";

export interface LiveEvent {
  type: string;
  data: Record<string, unknown>;
  receivedAt: number;
}

export function useAdminLive(enabled: boolean) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const token = authStore((s) => s.token);

  useEffect(() => {
    if (!enabled || !token) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${wsScheme}://${window.location.host}/ws/admin?token=${encodeURIComponent(
      token,
    )}`;
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        setEvents((prev) =>
          [{ ...parsed, receivedAt: Date.now() }, ...prev].slice(0, 50),
        );
      } catch {
        // ignore malformed
      }
    };

    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30_000);

    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [enabled, token]);

  return { events, connected };
}
