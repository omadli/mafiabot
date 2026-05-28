/**
 * Telegram link helpers.
 *
 * <TgUser>: renders a user as `<name>` + `@username` (clickable when
 *   username is present, otherwise plain text). Username opens the
 *   user's public Telegram profile.
 *
 * <TgGroup>: renders a group title. If `inviteLink` is provided, the
 *   title becomes an external link to that invite. Groups without an
 *   invite link render as plain text (no clickable link).
 *
 * `tgUserUrl(username)` and `tgGroupUrl(inviteLink)` are exported for
 * cases where callers need the URL directly (e.g. action buttons).
 *
 * Note: `tg://user?id=<id>` only resolves inside the Telegram app and
 * does nothing in a browser, so we only build a link when @username is
 * available. Pure-ID users render as plain text.
 */
import type { CSSProperties, ReactNode } from "react";

export function tgUserUrl(username: string | null | undefined): string | null {
  if (!username) return null;
  const clean = username.trim().replace(/^@/, "");
  return clean ? `https://t.me/${clean}` : null;
}

export function tgGroupUrl(inviteLink: string | null | undefined): string | null {
  if (!inviteLink) return null;
  const link = inviteLink.trim();
  if (!link) return null;
  // Accept full URLs or bare @public_group_handles.
  if (link.startsWith("http://") || link.startsWith("https://")) return link;
  if (link.startsWith("@")) return `https://t.me/${link.slice(1)}`;
  if (link.startsWith("t.me/")) return `https://${link}`;
  return link;
}

interface TgUserProps {
  id: number | string;
  firstName?: string | null;
  username?: string | null;
  /** When provided, wraps the visible name in an internal route link. */
  internalHref?: string;
  /** Render extra metadata under the name (e.g. join date). */
  meta?: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function TgUser({
  id,
  firstName,
  username,
  internalHref,
  meta,
  className,
  style,
}: TgUserProps) {
  const tgUrl = tgUserUrl(username);
  const displayName = firstName?.trim() || (username ? `@${username}` : `#${id}`);

  // Primary line: name (linked to internal detail page when provided).
  const primary = internalHref ? (
    <a href={internalHref} style={{ color: "inherit", textDecoration: "none" }}>
      {displayName}
    </a>
  ) : (
    <span>{displayName}</span>
  );

  // Secondary line: @username link or "—" placeholder.
  const secondary = tgUrl ? (
    <a
      href={tgUrl}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      style={{ color: "var(--muted)", textDecoration: "none", fontSize: "0.8rem" }}
      title="Open in Telegram"
    >
      @{username}
    </a>
  ) : (
    <span style={{ color: "var(--muted)", fontSize: "0.8rem" }}>—</span>
  );

  return (
    <div className={className} style={style}>
      <div>{primary}</div>
      <div>{secondary}</div>
      {meta && <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>{meta}</div>}
    </div>
  );
}

interface TgGroupProps {
  id?: number | string;
  title: string;
  inviteLink?: string | null;
  /** When provided, wraps the title in an internal route link. */
  internalHref?: string;
  className?: string;
  style?: CSSProperties;
  /** Show "🔗 t.me/..." under the title as a secondary clickable line. */
  showInvite?: boolean;
}

export function TgGroup({
  title,
  inviteLink,
  internalHref,
  className,
  style,
  showInvite = false,
}: TgGroupProps) {
  const url = tgGroupUrl(inviteLink);
  const primary = internalHref ? (
    <a href={internalHref} style={{ color: "inherit", textDecoration: "none" }}>
      {title || "—"}
    </a>
  ) : (
    <span>{title || "—"}</span>
  );

  return (
    <div className={className} style={style}>
      <div>{primary}</div>
      {showInvite && url && (
        <div>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{ color: "var(--muted)", textDecoration: "none", fontSize: "0.8rem" }}
            title="Open invite link"
          >
            🔗 {url.replace(/^https?:\/\//, "")}
          </a>
        </div>
      )}
    </div>
  );
}
