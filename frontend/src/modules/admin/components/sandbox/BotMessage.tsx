/**
 * One Telegram-style chat bubble for a single TranscriptEntry.
 *
 * Layout/styling lives in `sandbox.css` under `.sb-bubble*`.
 * All user-facing labels come from i18n.
 */

import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type { TranscriptEntry } from "@shared/api/sandbox";

import { renderBotText, type ParseMode } from "./botFormat";
import { KeyboardButton } from "./KeyboardButton";

interface BotMessageProps {
  entry: TranscriptEntry;
  onCallback?: (callbackData: string, messageId: number) => void;
  disabled?: boolean;
  compact?: boolean;
}

function timeLabel(ts: number): string {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function MediaChip({ media }: { media: NonNullable<TranscriptEntry["media"]> }) {
  const { t } = useTranslation();
  const label =
    media.type === "photo"
      ? `🖼 ${t("admin.sandbox.message.photo")}`
      : media.type === "animation"
        ? `🎞 ${t("admin.sandbox.message.animation")}`
        : media.type === "video"
          ? `🎬 ${t("admin.sandbox.message.video")}`
          : media.type === "invoice"
            ? `💎 ${t("admin.sandbox.message.invoice", { defaultValue: "invoice" })}`
            : `📎 ${media.type}`;
  return (
    <div className="sb-media" title={media.ref || ""}>
      {label}
      {media.caption ? <> — {media.caption.slice(0, 64)}</> : null}
    </div>
  );
}

export function BotMessage({ entry, onCallback, disabled, compact }: BotMessageProps) {
  const { t } = useTranslation();
  const edited = Boolean(entry.extra && entry.extra.edited);
  const deleted = Boolean(entry.extra && entry.extra.deleted);

  const headerLeft =
    entry.type === "toast"
      ? `🔔 ${t("admin.sandbox.message.toast", { defaultValue: "toast" })}`
      : entry.type === "edit"
        ? `✎ ${t("admin.sandbox.message.edit", { defaultValue: "edit" })}`
        : entry.type === "delete"
          ? `🗑 ${t("admin.sandbox.message.delete", { defaultValue: "delete" })}`
          : entry.type === "pin"
            ? `📌 ${t("admin.sandbox.message.pin", { defaultValue: "pin" })}`
            : entry.type === "unpin"
              ? `📍 ${t("admin.sandbox.message.unpin", { defaultValue: "unpin" })}`
              : `🤖 ${t("admin.sandbox.message.bot", { defaultValue: "Bot" })}`;

  const bodyNode = useMemo(
    () => renderBotText(entry.text, entry.parse_mode as ParseMode),
    [entry.text, entry.parse_mode],
  );

  const handleBtn = (cb: string) => onCallback?.(cb, entry.message_id);

  const className = [
    "sb-bubble",
    compact && "compact",
    entry.scope === "dm" && "dm",
    deleted && "deleted",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      <div className="sb-bubble-header">
        <span>
          {headerLeft} · {timeLabel(entry.ts)}
          {edited && (
            <span className="sb-bubble-edited" title={t("admin.sandbox.message.edited")}>
              ✎
            </span>
          )}
          {deleted && (
            <span className="sb-bubble-deleted" title={t("admin.sandbox.message.deleted")}>
              🗑
            </span>
          )}
        </span>
        <span className="sb-bubble-id">#{entry.message_id}</span>
      </div>

      {entry.media && <MediaChip media={entry.media} />}

      {bodyNode && <div className="sb-bubble-text">{bodyNode}</div>}

      {entry.reply_markup && entry.reply_markup.inline_keyboard.length > 0 && (
        <div className="sb-keyboard">
          {entry.reply_markup.inline_keyboard.map((row, rIdx) => (
            <div key={`r-${rIdx}`} className="sb-keyboard-row">
              {row.map((btn, bIdx) => (
                <KeyboardButton
                  key={`b-${rIdx}-${bIdx}`}
                  button={btn}
                  onCallback={onCallback ? handleBtn : undefined}
                  disabled={disabled || deleted}
                />
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
