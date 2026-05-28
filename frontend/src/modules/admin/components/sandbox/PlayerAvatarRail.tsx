/**
 * Vertical (desktop) / horizontal (mobile) rail of `PlayerChip`s with
 * sort + dead-toggle + keyboard shortcuts. Lives on the left of the
 * sandbox detail page.
 *
 * Keyboard:
 *   1-9, 0  → switch perspective by join_order
 *   [ / ]   → previous / next visible player (wraps)
 *   Shift+D → toggle "show dead"
 */

import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import type { LivePlayer } from "@shared/api/sandbox";

import { PlayerChip } from "./PlayerChip";

type SortMode = "join" | "recent";

interface PlayerAvatarRailProps {
  players: LivePlayer[];
  activeUserId: number | null;
  setActiveUserId: (uid: number) => void;
  lastMessageTs: Record<number, number>;
  lastSeenTs: Record<number, number>;
}

export function PlayerAvatarRail({
  players,
  activeUserId,
  setActiveUserId,
  lastMessageTs,
  lastSeenTs,
}: PlayerAvatarRailProps) {
  const { t } = useTranslation();
  const [sort, setSort] = useState<SortMode>("join");
  const [showDead, setShowDead] = useState(true);

  const visible = useMemo(() => {
    let list = [...players];
    if (!showDead) list = list.filter((p) => p.alive);
    if (sort === "recent") {
      list.sort(
        (a, b) =>
          (lastMessageTs[b.user_id] || 0) - (lastMessageTs[a.user_id] || 0),
      );
    } else {
      list.sort((a, b) => a.join_order - b.join_order);
    }
    return list;
  }, [players, showDead, sort, lastMessageTs]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tgt = e.target as HTMLElement;
      if (
        tgt &&
        (tgt.tagName === "INPUT" ||
          tgt.tagName === "TEXTAREA" ||
          tgt.tagName === "SELECT" ||
          tgt.isContentEditable)
      )
        return;

      if (e.key === "D" && e.shiftKey) {
        setShowDead((v) => !v);
        e.preventDefault();
        return;
      }
      if (/^[0-9]$/.test(e.key)) {
        const order = e.key === "0" ? 10 : parseInt(e.key, 10);
        const target = players.find((p) => p.join_order === order);
        if (target) {
          setActiveUserId(target.user_id);
          e.preventDefault();
        }
        return;
      }
      if (e.key === "[" || e.key === "]") {
        if (visible.length === 0) return;
        const idx = visible.findIndex((p) => p.user_id === activeUserId);
        const next =
          e.key === "]"
            ? visible[(idx + 1) % visible.length]
            : visible[(idx - 1 + visible.length) % visible.length];
        if (next) {
          setActiveUserId(next.user_id);
          e.preventDefault();
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [players, visible, activeUserId, setActiveUserId]);

  return (
    <div className="sb-rail">
      <div className="sb-rail-toolbar">
        <button
          type="button"
          onClick={() => setSort((s) => (s === "join" ? "recent" : "join"))}
          className="sb-rail-toggle"
          title={
            sort === "join"
              ? t("admin.sandbox.player_rail.sort_join")
              : t("admin.sandbox.player_rail.sort_recent")
          }
        >
          {sort === "join" ? "#" : "⏱"}
        </button>
        <button
          type="button"
          onClick={() => setShowDead((v) => !v)}
          className="sb-rail-toggle"
          title={t("admin.sandbox.player_rail.show_dead")}
          style={showDead ? undefined : { color: "var(--fg)" }}
        >
          {showDead ? "💀" : "👁"}
        </button>
      </div>

      {visible.map((p) => {
        const lastSeen = lastSeenTs[p.user_id] ?? 0;
        const lastMsg = lastMessageTs[p.user_id] ?? 0;
        const hasUnread = lastMsg > lastSeen;
        return (
          <PlayerChip
            key={p.user_id}
            userId={p.user_id}
            firstName={p.first_name}
            role={p.role}
            alive={p.alive}
            joinOrder={p.join_order}
            active={p.user_id === activeUserId}
            hasUnread={hasUnread}
            onClick={() => setActiveUserId(p.user_id)}
            tooltip={`${p.first_name} · ${p.role ?? "?"} · ${
              p.alive
                ? t("admin.sandbox.player.alive", { defaultValue: "alive" })
                : t("admin.sandbox.player.dead", { defaultValue: "dead" })
            }`}
          />
        );
      })}
    </div>
  );
}
