/**
 * Single source of truth for role + phase emoji used across the admin
 * dashboard (live game spectator, sandbox detail page, future replay
 * views). Names match `backend/app/core/roles/__init__.py::ROLE_REGISTRY`.
 */

/** All role codes in canonical team order (civilians, mafia, singletons).
 * Mirrors backend `DEFAULT_ROLES_ENABLED` / `ROLE_REGISTRY`. */
export const ROLE_CODES = [
  // Civilians (10)
  "citizen", "detective", "sergeant", "mayor", "doctor",
  "hooker", "hobo", "lucky", "suicide", "kamikaze",
  // Mafia (5)
  "don", "mafia", "lawyer", "journalist", "killer",
  // Singletons (6)
  "maniac", "werewolf", "mage", "arsonist", "crook", "snitch",
] as const;

export const ROLE_EMOJI: Record<string, string> = {
  // Civilians (10)
  citizen: "👨🏼",
  detective: "🕵🏻‍♂",
  sergeant: "👮🏻‍♂",
  mayor: "🎖",
  doctor: "👨🏻‍⚕",
  hooker: "💃",
  hobo: "🧙‍♂",
  lucky: "🤞🏼",
  suicide: "🤦🏼",
  kamikaze: "💣",
  // Mafia (5)
  don: "🤵🏻",
  mafia: "🤵🏼",
  lawyer: "👨‍💼",
  journalist: "👩🏼‍💻",
  killer: "🥷",
  // Singletons (6)
  maniac: "🔪",
  werewolf: "🐺",
  mage: "🧙",
  arsonist: "🧟",
  crook: "🤹",
  snitch: "🤓",
};

export const PHASE_EMOJI: Record<string, string> = {
  waiting: "📋",
  night: "🌙",
  day: "☀️",
  voting: "🗳",
  hanging_confirm: "⚖️",
  last_words: "💬",
  finished: "🏁",
  cancelled: "🚫",
};

/** Convenience: emoji + first_name for display lists. */
export function playerLabel(p: { role: string; first_name: string }): string {
  return `${ROLE_EMOJI[p.role] || ""} ${p.first_name}`;
}
