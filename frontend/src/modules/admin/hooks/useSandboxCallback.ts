/**
 * Hook for dispatching dashboard button-clicks as synthetic
 * CallbackQueries via the backend's `inject_callback` path.
 *
 * Returns a stable `fire` callback so consumers (the inline-keyboard
 * button component) don't memoize against a fresh mutate instance on
 * every render.
 *
 * Mutation success is intentionally silent — the WS `transcript_append`
 * event drives the UI update so we don't double-render. Errors surface
 * via the returned `error` for the component to toast.
 */

import { useCallback, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { sandboxApi } from "@shared/api/sandbox";
import type { SandboxCallbackRequest } from "@shared/api/sandbox";

export interface UseSandboxCallbackResult {
  fire: (payload: SandboxCallbackRequest) => void;
  error: string | null;
  pending: boolean;
  clearError: () => void;
}

export function useSandboxCallback(sandboxId: string | undefined): UseSandboxCallbackResult {
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: SandboxCallbackRequest) =>
      sandboxApi.callback(sandboxId!, payload),
    onError: (err: Error) =>
      setError(err.message || "callback failed"),
    onSuccess: () => setError(null),
  });

  const fire = useCallback(
    (payload: SandboxCallbackRequest) => {
      if (!sandboxId) return;
      setError(null);
      mutation.mutate(payload);
    },
    [sandboxId, mutation],
  );

  return {
    fire,
    error,
    pending: mutation.isPending,
    clearError: () => setError(null),
  };
}
