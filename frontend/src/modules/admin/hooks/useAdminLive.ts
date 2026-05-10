import { useEffect, useState } from "react";

import { authStore } from "@shared/store/auth";

export interface LiveEvent {
  type: string;
  data: Record<string, unknown>;
  receivedAt: number;
}

/**
 * Subscribe to admin live event stream over WebSocket.
 * Returns the latest events (capped at 50) and connection status.
 */
export function useAdminLive() {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const token = authStore((s) => s.token);

  useEffect(() => {
    if (!token) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${wsScheme}://${window.location.host}/ws/admin?token=${encodeURIComponent(token)}`;
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

    // Heartbeat (Telegram-friendly: keep connection open)
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30_000);

    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [token]);

  return { events, connected };
}
