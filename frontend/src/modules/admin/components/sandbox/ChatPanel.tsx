/**
 * Scrollable transcript pane for one chat (group / DM / mafia / dead).
 *
 * Behaviour:
 *   - Auto-scrolls to bottom on new messages IF the user is already
 *     pinned to the bottom. If they scrolled up to read older content,
 *     the viewport stays put.
 *   - Shows a sticky "↓ N new" pill when messages arrive while scrolled
 *     away; click jumps to the latest.
 *   - For very long transcripts (> 300 entries) we render only the
 *     last 300 and show a "showing last X of N" notice — keeps the DOM
 *     bounded without pulling in a virtualization library.
 *
 * Caller filters which entries belong here; this component is
 * stateless wrt to which chat is shown.
 */

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { TranscriptEntry } from "@shared/api/sandbox";

import { BotMessage } from "./BotMessage";

const MAX_RENDER = 300;

interface ChatPanelProps {
  entries: TranscriptEntry[];
  onCallback?: (callbackData: string, messageId: number) => void;
  disabled?: boolean;
  compact?: boolean;
  emptyLabel?: string;
  initialScrollTop?: number;
  onScrollChange?: (scrollTop: number) => void;
}

export function ChatPanel({
  entries,
  onCallback,
  disabled,
  compact,
  emptyLabel,
  initialScrollTop,
  onScrollChange,
}: ChatPanelProps) {
  const { t } = useTranslation();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [atBottom, setAtBottom] = useState(true);
  const [unseenCount, setUnseenCount] = useState(0);
  const prevLenRef = useRef(entries.length);

  useLayoutEffect(() => {
    if (scrollRef.current && initialScrollTop != null) {
      scrollRef.current.scrollTop = initialScrollTop;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const grew = entries.length > prevLenRef.current;
    const delta = entries.length - prevLenRef.current;
    prevLenRef.current = entries.length;
    if (!grew || !scrollRef.current) return;
    if (atBottom) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setUnseenCount(0);
    } else {
      setUnseenCount((c) => c + Math.max(1, delta));
    }
  }, [entries.length, atBottom]);

  const onScroll: React.UIEventHandler<HTMLDivElement> = (e) => {
    const el = e.currentTarget;
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 8;
    if (isAtBottom !== atBottom) setAtBottom(isAtBottom);
    if (isAtBottom) setUnseenCount(0);
    onScrollChange?.(el.scrollTop);
  };

  const jumpToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setAtBottom(true);
      setUnseenCount(0);
    }
  };

  const visible = entries.length > MAX_RENDER ? entries.slice(-MAX_RENDER) : entries;
  const truncated = entries.length - visible.length;

  return (
    <div style={{ position: "relative", height: "100%", display: "flex", flexDirection: "column" }}>
      <div ref={scrollRef} onScroll={onScroll} className="sb-chat-scroll">
        {truncated > 0 && (
          <div className="sb-chat-truncated">
            {t("admin.sandbox.detail.showing_last_n_of_x", {
              shown: visible.length,
              total: entries.length,
              defaultValue: "… showing last {{shown}} of {{total}} messages",
            })}
          </div>
        )}
        {visible.length === 0 ? (
          <div className="sb-chat-empty">
            {emptyLabel ?? t("admin.sandbox.detail.chat_empty", { defaultValue: "(no messages)" })}
          </div>
        ) : (
          visible.map((e) => (
            <BotMessage
              key={`${e.seq}-${e.message_id}`}
              entry={e}
              onCallback={onCallback}
              disabled={disabled}
              compact={compact}
            />
          ))
        )}
      </div>

      {!atBottom && unseenCount > 0 && (
        <button type="button" onClick={jumpToBottom} className="sb-jump-pill">
          ↓ {t("admin.sandbox.detail.n_new", { count: unseenCount, defaultValue: "{{count}} new" })}
        </button>
      )}
    </div>
  );
}
