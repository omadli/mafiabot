/**
 * Sandbox transcript stream — initial fetch + incremental WS append.
 *
 * The transcript can grow to thousands of entries, so we never re-fetch
 * the whole list on a delta event. Instead:
 *   - Initial load: react-query GET /transcript (paginated by `since`)
 *   - Live: `useSandboxStream` forwards `transcript_append` → we splice
 *     into the cache via `setQueryData`.
 *   - Reconnect: refetch with `since = lastSeq` to fill any gap.
 *
 * Edits / deletes mutate the matching entry in place so chat-bubble
 * components can show "✎ edited" without re-rendering the whole pane.
 */

import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { sandboxApi } from "@shared/api/sandbox";
import type { TranscriptEntry } from "@shared/api/sandbox";

import { useSandboxStream } from "./useSandboxStream";

export interface SandboxTranscriptResult {
  entries: TranscriptEntry[];
  isLoading: boolean;
  wsConnected: boolean;
}

const queryKey = (sandboxId: string | undefined) => ["sandbox-transcript", sandboxId];

export function useSandboxTranscript(
  sandboxId: string | undefined,
): SandboxTranscriptResult {
  const qc = useQueryClient();
  const lastSeqRef = useRef(0);

  const query = useQuery({
    queryKey: queryKey(sandboxId),
    queryFn: async () => {
      // Page through any backlog so we never truncate the chat view.
      const collected: TranscriptEntry[] = [];
      let since = 0;
      // Hard guard: stop after 50 pages (10k entries) — well above our
      // server-side cap, so this should never trigger in practice.
      for (let i = 0; i < 50; i++) {
        const page = await sandboxApi.transcript(sandboxId!, since, 200);
        collected.push(...page.entries);
        if (page.entries.length < 200) break;
        since = page.next_since;
      }
      lastSeqRef.current =
        collected.length > 0 ? collected[collected.length - 1].seq : 0;
      return collected;
    },
    enabled: !!sandboxId,
    retry: false,
    staleTime: 60_000,
  });

  const { wsConnected } = useSandboxStream(sandboxId, {
    onTranscriptAppend: (entry) => {
      // De-dupe — a slow handler + reconnect may replay an entry; trust
      // the monotonic `seq` to skip what we've already shown.
      qc.setQueryData<TranscriptEntry[]>(queryKey(sandboxId), (prev) => {
        const list = prev ?? [];
        if (list.length > 0 && list[list.length - 1].seq >= entry.seq) {
          return list;
        }
        // edit/delete in place when ref_message_id matches an existing send.
        if (entry.type === "edit" && entry.ref_message_id) {
          const idx = list.findIndex(
            (e) => e.message_id === entry.ref_message_id && e.type === "send",
          );
          if (idx >= 0) {
            const next = list.slice();
            next[idx] = {
              ...next[idx],
              text: entry.text ?? next[idx].text,
              reply_markup: entry.reply_markup ?? next[idx].reply_markup,
              extra: { ...(next[idx].extra ?? {}), edited: true, edit_seq: entry.seq },
            };
            return next;
          }
        }
        if (entry.type === "delete" && entry.ref_message_id) {
          const idx = list.findIndex(
            (e) => e.message_id === entry.ref_message_id,
          );
          if (idx >= 0) {
            const next = list.slice();
            next[idx] = {
              ...next[idx],
              extra: { ...(next[idx].extra ?? {}), deleted: true },
            };
            return next;
          }
        }
        lastSeqRef.current = entry.seq;
        return [...list, entry];
      });
    },
  });

  // On reconnect (wsConnected flipped false→true with existing data),
  // fill any gap via a since-query so we don't lose deltas during the
  // dead window.
  const prevWsRef = useRef(wsConnected);
  useEffect(() => {
    if (!sandboxId) return;
    const justReconnected = !prevWsRef.current && wsConnected;
    prevWsRef.current = wsConnected;
    if (!justReconnected || lastSeqRef.current === 0) return;
    (async () => {
      try {
        const page = await sandboxApi.transcript(sandboxId, lastSeqRef.current, 1000);
        if (page.entries.length === 0) return;
        qc.setQueryData<TranscriptEntry[]>(queryKey(sandboxId), (prev) => {
          const list = prev ?? [];
          const known = new Set(list.map((e) => e.seq));
          const fresh = page.entries.filter((e) => !known.has(e.seq));
          if (fresh.length === 0) return list;
          lastSeqRef.current = fresh[fresh.length - 1].seq;
          return [...list, ...fresh];
        });
      } catch {
        // Best-effort: a failed gap-fill is recoverable on the next
        // state_changed → invalidate path.
      }
    })();
  }, [wsConnected, sandboxId, qc]);

  return {
    entries: query.data ?? [],
    isLoading: query.isLoading,
    wsConnected,
  };
}
