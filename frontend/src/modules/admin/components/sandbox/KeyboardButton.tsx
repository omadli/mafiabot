/**
 * One Telegram inline-keyboard button.
 *
 * Three button types map to three behaviours:
 *   - URL button     → renders as `<a target="_blank">`, never a callback
 *   - Callback       → onClick fires the sandbox `inject_callback` flow
 *   - Static / inactive → label-only chip (e.g. switch_inline_query)
 */

import type { InlineKeyboardButton } from "@shared/api/sandbox";

interface KeyboardButtonProps {
  button: InlineKeyboardButton;
  onCallback?: (callbackData: string) => void;
  disabled?: boolean;
}

export function KeyboardButton({ button, onCallback, disabled }: KeyboardButtonProps) {
  if (button.url) {
    return (
      <a
        href={button.url}
        target="_blank"
        rel="noopener noreferrer"
        title={button.url}
        className="sb-kb-btn url"
      >
        🔗 {button.text}
      </a>
    );
  }

  if (button.callback_data && onCallback) {
    return (
      <button
        type="button"
        className="sb-kb-btn"
        title={button.callback_data}
        disabled={disabled}
        onClick={() => onCallback(button.callback_data!)}
      >
        {button.text}
      </button>
    );
  }

  return (
    <span className="sb-kb-btn static" title={button.callback_data}>
      {button.text}
    </span>
  );
}
