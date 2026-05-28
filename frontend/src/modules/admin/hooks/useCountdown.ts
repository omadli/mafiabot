import { useEffect, useState } from "react";

/**
 * Tick a 1-second countdown to a unix-seconds `deadline`. Returns the
 * remaining seconds (>= 0). `null` deadline → returns 0 and no interval
 * is set up — safe to use as the live game's `phase_ends_at` which is
 * null during indefinite registration.
 */
export function useCountdown(deadline: number | null): number {
  const [now, setNow] = useState(() => Math.floor(Date.now() / 1000));
  useEffect(() => {
    if (!deadline) return;
    const t = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000);
    return () => clearInterval(t);
  }, [deadline]);
  return deadline ? Math.max(0, deadline - now) : 0;
}
