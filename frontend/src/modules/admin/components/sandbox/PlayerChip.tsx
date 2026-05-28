/**
 * Avatar tile in the left rail (40-ish px) — stacks vertically on
 * desktop, horizontally on mobile.
 */

import { ROLE_EMOJI } from "../../constants/roles";

interface PlayerChipProps {
  userId: number;
  firstName: string;
  role: string | null;
  alive: boolean;
  joinOrder: number;
  active: boolean;
  hasUnread: boolean;
  tooltip?: string;
  onClick: () => void;
}

export function PlayerChip({
  firstName,
  role,
  alive,
  joinOrder,
  active,
  hasUnread,
  tooltip,
  onClick,
}: PlayerChipProps) {
  const emoji = (role && ROLE_EMOJI[role]) || firstName.charAt(0).toUpperCase();
  const className = [
    "sb-chip",
    active && "active",
    !alive && "dead",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type="button"
      onClick={onClick}
      title={tooltip || `${firstName}${role ? ` (${role})` : ""}`}
      className={className}
    >
      <span className="sb-chip-emoji">{emoji}</span>
      <span className="sb-chip-order">{joinOrder}</span>
      {!alive && <span className="sb-chip-dead-badge">💀</span>}
      {hasUnread && alive && <span className="sb-chip-unread" />}
    </button>
  );
}
