/**
 * Live game-state hook for a sandbox session.
 *
 * Mirrors `useLiveGame` (real-game spectator) but targets the
 * `/api/sa/sandbox/games/{id}/*` endpoints. State updates flow through
 * the same WebSocket channel as real games (per-group filter) — the
 * sandbox just registers under its `fake_group_id`.
 *
 * Two complementary hooks live in `useSandboxTranscript` and
 * `useSandboxStream` (the WS layer). Detail page wires all three.
 */

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { sandboxApi } from "@shared/api/sandbox";
import type { LiveGameState } from "@shared/api/sandbox";

import { useSandboxStream } from "./useSandboxStream";

export interface SandboxGameResult {
  state: LiveGameState | undefined;
  isLoading: boolean;
  error: unknown;
  wsConnected: boolean;
}

export function useSandboxGame(sandboxId: string | undefined): SandboxGameResult {
  const qc = useQueryClient();

  const query = useQuery({
    queryKey: ["sandbox-state", sandboxId],
    queryFn: () => sandboxApi.state(sandboxId!),
    enabled: !!sandboxId,
    retry: false,
  });

  // Forward `state_changed` from the WS stream into a query invalidation
  // so the snapshot refetches without us re-implementing the merge.
  const { wsConnected } = useSandboxStream(
    sandboxId,
    {
      onStateChanged: () =>
        qc.invalidateQueries({ queryKey: ["sandbox-state", sandboxId] }),
    },
  );

  // Auto-clean stale state when the URL switches between sandboxes.
  useEffect(() => {
    return () => {
      qc.cancelQueries({ queryKey: ["sandbox-state", sandboxId] });
    };
  }, [sandboxId, qc]);

  return {
    state: query.data,
    isLoading: query.isLoading,
    error: query.error,
    wsConnected,
  };
}
