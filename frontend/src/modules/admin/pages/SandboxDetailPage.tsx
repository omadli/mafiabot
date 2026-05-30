/**
 * The "everything" view: super-admin watches + drives a sandbox game.
 *
 * Layout (CSS Grid, see sandbox.css for responsive breakpoints):
 *   ┌────────────────────────────────────────────────────┐
 *   │ Header (status, round, countdown, WS)              │
 *   ├────┬──────────────┬──────────────┬─────────────────┤
 *   │ Av │ Group chat   │ Active DM    │ Game state      │
 *   │ R  │  (tabs+pane) │  (player ↔ bot) │ (roles/votes)│
 *   ├────┴──────────────┴──────────────┴─────────────────┤
 *   │ [⏭ Skip] [⏹ Stop] [🔁 Restart] [🗑 Destroy]        │
 *   └────────────────────────────────────────────────────┘
 *
 * Below 1100px the right sidebar drops below the chats; below 760px
 * everything stacks and the avatar rail flips to horizontal.
 */

import { Link, useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";

import { sandboxApi } from "@shared/api/sandbox";
import type { LivePlayer } from "@shared/api/sandbox";

import { PHASE_EMOJI } from "../constants/roles";
import { useCountdown } from "../hooks/useCountdown";
import { useSandboxGame } from "../hooks/useSandboxGame";
import { useSandboxTranscript } from "../hooks/useSandboxTranscript";
import { useSandboxCallback } from "../hooks/useSandboxCallback";
import { useSandboxControls } from "../hooks/useSandboxControls";

import { ChatPanel } from "../components/sandbox/ChatPanel";
import {
  ChatSelectorTabs,
  type ChatTab,
} from "../components/sandbox/ChatSelectorTabs";
import { GameStateSidebar } from "../components/sandbox/GameStateSidebar";
import { PhaseControlBar } from "../components/sandbox/PhaseControlBar";
import { PlayerAvatarRail } from "../components/sandbox/PlayerAvatarRail";
import "../components/sandbox/sandbox.css";

function fmtSeconds(s: number): string {
  if (s <= 0) return "0:00";
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${m}:${ss.toString().padStart(2, "0")}`;
}

export function SandboxDetailPage() {
  const { t } = useTranslation();
  const { sandboxId } = useParams<{ sandboxId: string }>();

  const { data: detail } = useQuery({
    queryKey: ["sandbox-detail", sandboxId],
    queryFn: () => sandboxApi.get(sandboxId!),
    enabled: !!sandboxId,
  });

  const { state, isLoading, error, wsConnected } = useSandboxGame(sandboxId);
  const { entries } = useSandboxTranscript(sandboxId);
  const callback = useSandboxCallback(sandboxId);
  const controls = useSandboxControls(sandboxId);

  const [activeUserId, setActiveUserId] = useState<number | null>(null);
  useEffect(() => {
    if (activeUserId !== null) return;
    const hash = window.location.hash.match(/#p=(-?\d+)/);
    if (hash) {
      setActiveUserId(parseInt(hash[1], 10));
      return;
    }
    const fallback =
      state?.players?.[0]?.user_id ??
      detail?.fake_users_snapshot?.[0]?.user_id ??
      null;
    if (fallback != null) setActiveUserId(fallback);
  }, [activeUserId, state, detail]);

  useEffect(() => {
    if (activeUserId == null) return;
    const newHash = `#p=${activeUserId}`;
    if (window.location.hash !== newHash) {
      window.history.replaceState(
        null,
        "",
        `${window.location.pathname}${window.location.search}${newHash}`,
      );
    }
  }, [activeUserId]);

  const lastMessageTs = useMemo(() => {
    const out: Record<number, number> = {};
    for (const e of entries) {
      const uid = e.scope === "dm" ? e.target_user_id : null;
      if (uid != null) out[uid] = Math.max(out[uid] ?? 0, e.ts);
    }
    return out;
  }, [entries]);

  const [lastSeenTs, setLastSeenTs] = useState<Record<number, number>>({});
  useEffect(() => {
    if (activeUserId == null) return;
    setLastSeenTs((prev) => ({ ...prev, [activeUserId]: Date.now() / 1000 }));
  }, [activeUserId]);

  const [chatTab, setChatTab] = useState<ChatTab>("group");
  const counts = useMemo(() => {
    const c: Record<ChatTab, number> = { group: 0, dm: 0, mafia_chat: 0, dead_chat: 0 };
    for (const e of entries) {
      c[e.scope as ChatTab] = (c[e.scope as ChatTab] ?? 0) + 1;
    }
    return c;
  }, [entries]);

  const groupEntries = useMemo(
    () => entries.filter((e) => e.scope === chatTab),
    [entries, chatTab],
  );
  const dmEntries = useMemo(
    () =>
      activeUserId != null
        ? entries.filter(
            (e) => e.scope === "dm" && e.target_user_id === activeUserId,
          )
        : [],
    [entries, activeUserId],
  );

  const remaining = useCountdown(state?.phase_ends_at ?? null);

  const onGroupClick = (cb: string, msgId: number) => {
    if (activeUserId == null || !detail) return;
    callback.fire({
      user_id: activeUserId,
      callback_data: cb,
      message_id: msgId,
      chat_id: detail.fake_group_id,
    });
  };
  const onDmClick = (cb: string, msgId: number) => {
    if (activeUserId == null) return;
    callback.fire({
      user_id: activeUserId,
      callback_data: cb,
      message_id: msgId,
    });
  };

  // Operator types as the active player. DM channel uses the user's own
  // chat_id (private scope). Group channel uses fake_group_id so the
  // dispatcher routes it through the group handlers (currently unused
  // by the engine but handy for future testing).
  const onGroupSend = async (text: string) => {
    if (activeUserId == null || !sandboxId || !detail) return;
    await sandboxApi.message(sandboxId, {
      user_id: activeUserId,
      text,
      chat_id: detail.fake_group_id,
    });
  };
  const onDmSend = async (text: string) => {
    if (activeUserId == null || !sandboxId) return;
    await sandboxApi.message(sandboxId, { user_id: activeUserId, text });
  };

  const activePlayer: LivePlayer | undefined = state?.players.find(
    (p) => p.user_id === activeUserId,
  );

  if (!sandboxId) return null;

  if (isLoading) {
    return <div className="admin-card">⏳ {t("loading")}</div>;
  }

  if (error) {
    return (
      <div className="admin-card" style={{ color: "var(--sb-err)" }}>
        ⚠️ {t("admin.sandbox.errors.game_not_found")}
        <div style={{ marginTop: "0.5rem" }}>
          <Link to="/admin/sandbox" className="admin-btn">
            ← {t("admin.sandbox.detail.back_to_list")}
          </Link>
        </div>
      </div>
    );
  }

  if (!state || !detail) return null;

  return (
    <div className="sb-detail">
      {/* === Header === */}
      <div className="admin-card sb-detail-header">
        <h2 className="sb-detail-title">
          🧪 {t("admin.sandbox.detail.header_sandbox")}{" "}
          <code>#{sandboxId.slice(0, 8)}</code>
        </h2>
        <span className="sb-detail-pill">
          {PHASE_EMOJI[state.phase] || ""} <strong>{state.phase}</strong>
        </span>
        <span className="sb-detail-pill">
          {t("admin.sandbox.sidebar.round")} {state.round_num}
        </span>
        {state.phase_ends_at && remaining > 0 && (
          <span className="sb-detail-pill muted">⏱ {fmtSeconds(remaining)}</span>
        )}
        <span className="sb-detail-pill muted">
          {state.players.filter((p) => p.alive).length}/{state.players.length}{" "}
          {t("admin.sandbox.sidebar.alive")}
        </span>
        <span className={`sb-detail-pill ${wsConnected ? "ok" : "err"}`}>
          {wsConnected ? "🟢" : "🔴"} WS
        </span>
        <span className="sb-detail-pill muted">
          {t("admin.sandbox.list.col_mode")}: {detail.auto_play_mode}
        </span>
        <div className="sb-detail-spacer" />
        <Link to="/admin/sandbox" className="admin-btn small">
          ← {t("admin.sandbox.detail.back_to_list")}
        </Link>
      </div>

      {/* === Main grid === */}
      <div className="sb-detail-body">
        {/* Avatar rail */}
        <div className="admin-card sb-panel sb-rail-card">
          <PlayerAvatarRail
            players={state.players}
            activeUserId={activeUserId}
            setActiveUserId={setActiveUserId}
            lastMessageTs={lastMessageTs}
            lastSeenTs={lastSeenTs}
          />
        </div>

        {/* Group chat panel */}
        <div className="admin-card sb-panel">
          <ChatSelectorTabs active={chatTab} onChange={setChatTab} counts={counts} />
          <div className="sb-panel-body">
            <ChatPanel
              entries={groupEntries}
              onCallback={onGroupClick}
              onSendMessage={chatTab === "group" ? onGroupSend : undefined}
              inputPlaceholder={
                activePlayer
                  ? t("admin.sandbox.detail.input_placeholder_named", {
                      name: activePlayer.first_name,
                      defaultValue: `Type as ${activePlayer.first_name}…`,
                    })
                  : undefined
              }
              disabled={callback.pending}
              emptyLabel={t("admin.sandbox.detail.group_empty")}
            />
          </div>
        </div>

        {/* Active DM panel */}
        <div className="admin-card sb-panel">
          <div className="sb-panel-header">
            📩 {t("admin.sandbox.detail.perspective_label")}{" "}
            <strong>{activePlayer?.first_name ?? "—"}</strong>{" "}
            {activePlayer && (
              <code style={{ color: "var(--muted)", marginLeft: "0.25rem" }}>
                {activePlayer.role ?? "?"} ·{" "}
                {activePlayer.alive
                  ? t("admin.sandbox.player.alive")
                  : t("admin.sandbox.player.dead")}
              </code>
            )}
          </div>
          <div className="sb-panel-body">
            <ChatPanel
              entries={dmEntries}
              onCallback={onDmClick}
              onSendMessage={activeUserId != null ? onDmSend : undefined}
              inputPlaceholder={
                activePlayer
                  ? t("admin.sandbox.detail.input_placeholder_dm", {
                      name: activePlayer.first_name,
                      defaultValue: `Type as ${activePlayer.first_name}…`,
                    })
                  : undefined
              }
              disabled={callback.pending}
              compact
              emptyLabel={t("admin.sandbox.detail.dm_empty")}
            />
          </div>
        </div>

        {/* Game state sidebar */}
        <div className="admin-card sb-panel sb-sidebar-card">
          <GameStateSidebar state={state} activeUserId={activeUserId} />
        </div>
      </div>

      {/* === Bottom controls === */}
      <PhaseControlBar
        sandboxId={sandboxId}
        status={detail.status}
        controls={controls}
      />
    </div>
  );
}
