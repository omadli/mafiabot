/**
 * Bottom controls bar — phase advance + pause + restart + destroy.
 *
 * The "Start" button shows while a CREATED sandbox is awaiting kickoff;
 * otherwise the bar renders runtime controls. Destroy uses the typed
 * confirm modal so accidental clicks can't blow away a session.
 */

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { sandboxApi } from "@shared/api/sandbox";
import type { SandboxStatus } from "@shared/api/sandbox";

import type { UseSandboxControlsResult } from "../../hooks/useSandboxControls";
import { DestroyConfirmModal } from "./DestroyConfirmModal";

interface PhaseControlBarProps {
  sandboxId: string;
  status: SandboxStatus;
  controls: UseSandboxControlsResult;
}

export function PhaseControlBar({
  sandboxId,
  status,
  controls,
}: PhaseControlBarProps) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [destroyOpen, setDestroyOpen] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const isCreated = status === "created";
  const isTerminal =
    status === "finished" || status === "destroyed" || status === "errored";
  const isRunning = status === "running";

  const startNow = async () => {
    setStartError(null);
    setStarting(true);
    try {
      await sandboxApi.start(sandboxId);
      // Refresh the detail query so the toolbar drops the Start button and
      // the rest of the dashboard sees the new "running" status. Without
      // this, the second click on a still-CREATED-looking UI hits the
      // backend with the session already RUNNING.
      await qc.invalidateQueries({ queryKey: ["sandbox-detail", sandboxId] });
      qc.invalidateQueries({ queryKey: ["sandbox-state", sandboxId] });
      qc.invalidateQueries({ queryKey: ["sandbox-list"] });
    } catch (e) {
      setStartError((e as Error).message || t("admin.sandbox.errors.start_failed"));
    } finally {
      setStarting(false);
    }
  };

  return (
    <>
      <div className="sb-controls">
        {isCreated && (
          <button
            type="button"
            className="admin-btn primary"
            onClick={startNow}
            disabled={starting}
          >
            {starting
              ? `⏳ ${t("admin.sandbox.controls.starting")}`
              : `🚀 ${t("admin.sandbox.controls.start")}`}
          </button>
        )}

        {isRunning && (
          <button
            type="button"
            className="admin-btn"
            onClick={controls.advance}
            disabled={controls.pending}
            title={t("admin.sandbox.controls.skip")}
          >
            ⏭ {t("admin.sandbox.controls.skip")}
          </button>
        )}

        {(isRunning || isCreated) && (
          <button
            type="button"
            className="admin-btn"
            onClick={controls.stop}
            disabled={controls.pending}
            title={t("admin.sandbox.controls.stop_keep_history")}
          >
            ⏹ {t("admin.sandbox.controls.stop")}
          </button>
        )}

        <button
          type="button"
          className="admin-btn"
          onClick={controls.restart}
          disabled={controls.pending}
          title={t("admin.sandbox.controls.restart_hint")}
        >
          🔁 {t("admin.sandbox.controls.restart")}
        </button>

        <button
          type="button"
          className="admin-btn danger"
          onClick={() => setDestroyOpen(true)}
          disabled={controls.pending}
          title={t("admin.sandbox.controls.destroy_hint")}
        >
          🗑 {t("admin.sandbox.controls.destroy")}
        </button>

        <div className="sb-controls-spacer" />

        {(controls.error || startError) && (
          <span
            className="sb-controls-error"
            onClick={() => {
              controls.clearError();
              setStartError(null);
            }}
            title={t("admin.sandbox.errors.click_to_dismiss")}
          >
            ⚠️ {controls.error || startError}
          </span>
        )}

        {isTerminal && (
          <span className="sb-controls-status">
            {t(`admin.sandbox.list.status_${status}`)}
          </span>
        )}
      </div>

      <DestroyConfirmModal
        open={destroyOpen}
        onClose={() => setDestroyOpen(false)}
        onConfirm={() => {
          setDestroyOpen(false);
          controls.destroy();
        }}
      />
    </>
  );
}
