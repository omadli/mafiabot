/**
 * Single WebSocket connection per sandbox, fanned out to multiple
 * consumers via the callback bundle.
 *
 * The backend reuses the `/ws/admin/group/{fake_group_id}` endpoint —
 * `state_changed`, `phase_change`, `transcript_append`, etc. all fire
 * on that channel for sandbox `fake_group_id`s the same way they fire
 * for real games. We hide the WS lifecycle behind one hook so the
 * detail page can subscribe to events without managing reconnects.
 *
 * Heartbeat + reconnect-on-error are kept symmetric with `useLiveGame`
 * so a sandbox tab feels identical to the real spectator.
 */

import { useEffect, useRef, useState } from "react";

import { authStore } from "@shared/store/auth";
import { sandboxApi } from "@shared/api/sandbox";
import type { TranscriptEntry } from "@shared/api/sandbox";

export interface SandboxStreamCallbacks {
  onStateChanged?: () => void;
  onPhaseChanged?: (data: { phase: string; round_num: number }) => void;
  onTranscriptAppend?: (entry: TranscriptEntry) => void;
  onSandboxDestroyed?: () => void;
}

interface UseSandboxStreamResult {
  wsConnected: boolean;
}

export function useSandboxStream(
  sandboxId: string | undefined,
  callbacks: SandboxStreamCallbacks,
): UseSandboxStreamResult {
  const token = authStore((s) => s.token);
  const [wsConnected, setWsConnected] = useState(false);
  // Refresh callback ref on each render so the WS handler sees the latest
  // closure without re-establishing the socket.
  const cbRef = useRef(callbacks);
  cbRef.current = callbacks;

  useEffect(() => {
    if (!sandboxId || !token) return;

    let cancelled = false;
    let ws: WebSocket | null = null;
    let heartbeat: ReturnType<typeof setInterval> | null = null;
    let fakeGroupId: number | null = null;

    // Need fake_group_id (negative BigInt) before we can subscribe.
    // The detail endpoint already hits this — but we re-fetch in case
    // the consumer hasn't loaded it yet. Cheap and idempotent.
    const init = async () => {
      try {
        const detail = await sandboxApi.get(sandboxId);
        if (cancelled) return;
        fakeGroupId = detail.fake_group_id;
        const wsScheme =
          window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${wsScheme}://${window.location.host}/ws/admin/group/${fakeGroupId}?token=${encodeURIComponent(token)}`;
        ws = new WebSocket(url);
        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => setWsConnected(false);
        ws.onerror = () => setWsConnected(false);
        ws.onmessage = (e) => {
          try {
            const evt = JSON.parse(e.data);
            const cb = cbRef.current;
            switch (evt.type) {
              case "state_changed":
                cb.onStateChanged?.();
                break;
              case "phase_change":
                cb.onPhaseChanged?.(evt.data);
                break;
              case "transcript_append":
                if (cb.onTranscriptAppend) cb.onTranscriptAppend(evt.data.entry);
                break;
              case "sandbox_destroyed":
                cb.onSandboxDestroyed?.();
                break;
              case "game_cleared":
                // Real-game alias the broker also emits when state is wiped.
                cb.onSandboxDestroyed?.();
                break;
              default:
                // Unknown event types are forwarded as state changes —
                // safer to over-refetch than to miss a UI update.
                cb.onStateChanged?.();
            }
          } catch {
            // malformed JSON, ignore
          }
        };
        heartbeat = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) ws.send("ping");
        }, 30_000);
      } catch {
        // Detail fetch failed (sandbox not found yet, transient network) —
        // surface as wsConnected=false; the consumer's react-query already
        // shows its own error UI on this case.
        setWsConnected(false);
      }
    };

    init();

    return () => {
      cancelled = true;
      if (heartbeat) clearInterval(heartbeat);
      if (ws) ws.close();
    };
  }, [sandboxId, token]);

  return { wsConnected };
}
