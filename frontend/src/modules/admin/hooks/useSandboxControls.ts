/**
 * Phase-control bar hook — bundles the lifecycle mutations the dashboard
 * exposes as buttons (advance, stop, restart, destroy).
 *
 * Each mutation returns a `pending` flag so the toolbar can disable its
 * own button without managing per-action loading state. `error` is the
 * single most-recent error across all four — the toolbar surfaces it as
 * a transient toast.
 */

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { sandboxApi } from "@shared/api/sandbox";

export interface UseSandboxControlsResult {
  advance: () => void;
  stop: () => void;
  restart: () => void;
  destroy: () => void;
  pending: boolean;
  error: string | null;
  clearError: () => void;
}

export function useSandboxControls(sandboxId: string | undefined): UseSandboxControlsResult {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const onMutate = () => setError(null);
  const onError = (e: Error) => setError(e.message || "Action failed");
  const onMutationSuccess = () => {
    qc.invalidateQueries({ queryKey: ["sandbox-state", sandboxId] });
    qc.invalidateQueries({ queryKey: ["sandbox-detail", sandboxId] });
  };

  const advanceMutation = useMutation({
    mutationFn: () => sandboxApi.advance(sandboxId!),
    onMutate,
    onError,
    onSuccess: onMutationSuccess,
  });

  const stopMutation = useMutation({
    mutationFn: () => sandboxApi.stop(sandboxId!),
    onMutate,
    onError,
    onSuccess: onMutationSuccess,
  });

  const restartMutation = useMutation({
    mutationFn: () => sandboxApi.restart(sandboxId!),
    onMutate,
    onError,
    onSuccess: (newDetail) => {
      qc.invalidateQueries({ queryKey: ["sandbox-list"] });
      navigate(`/admin/sandbox/${newDetail.sandbox_id}`);
    },
  });

  const destroyMutation = useMutation({
    mutationFn: () => sandboxApi.destroy(sandboxId!),
    onMutate,
    onError,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sandbox-list"] });
      navigate("/admin/sandbox");
    },
  });

  const pending =
    advanceMutation.isPending ||
    stopMutation.isPending ||
    restartMutation.isPending ||
    destroyMutation.isPending;

  return {
    advance: () => sandboxId && advanceMutation.mutate(),
    stop: () => sandboxId && stopMutation.mutate(),
    restart: () => sandboxId && restartMutation.mutate(),
    destroy: () => sandboxId && destroyMutation.mutate(),
    pending,
    error,
    clearError: () => setError(null),
  };
}
