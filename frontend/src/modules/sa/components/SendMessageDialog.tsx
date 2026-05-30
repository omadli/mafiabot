/**
 * Free-form admin → user DM dialog.
 *
 * Mounts as a modal on both the website's `/admin/users/:id` page and
 * the WebApp's `/webapp/sa/users/:id` page. Submits to whichever
 * backend prefix matches the active auth via `superAdminApi.sendUserMessage`.
 *
 * The bot wraps the typed text in a localised "Super Admindan sizga
 * xabar: <i>…</i>" envelope so the user always sees it as an official
 * admin message, regardless of the source surface.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";

import { superAdminApi } from "@shared/api/superAdmin";

interface SendMessageDialogProps {
  userId: number;
  userName: string;
  open: boolean;
  onClose: () => void;
  /** Optional callback fired after a successful send (for toasts/refresh). */
  onSent?: () => void;
}

export function SendMessageDialog({
  userId,
  userName,
  open,
  onClose,
  onSent,
}: SendMessageDialogProps) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const submit = async () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setBusy(true);
    setError(null);
    try {
      await superAdminApi.sendUserMessage(userId, trimmed);
      setText("");
      onSent?.();
      onClose();
    } catch (e) {
      setError((e as Error).message || t("sa.send_msg.error_send_failed", "Send failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="sa-modal-backdrop"
      onClick={(e) => {
        // Click outside the panel to close.
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="sa-modal-panel">
        <h3 style={{ margin: "0 0 0.25rem" }}>
          💬 {t("sa.send_msg.title", "Send message to user")}
        </h3>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 0 }}>
          {t("sa.send_msg.subtitle", "Recipient")}: <strong>{userName}</strong> (#{userId})
        </p>

        <textarea
          className="sa-modal-textarea"
          rows={5}
          maxLength={4096}
          autoFocus
          placeholder={t(
            "sa.send_msg.placeholder",
            "Your message — delivered as Super Admin DM…",
          )}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={busy}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            color: "var(--muted)",
            fontSize: "0.8rem",
            marginTop: "0.25rem",
          }}
        >
          <span>{t("sa.send_msg.envelope_hint", "Bot wraps your text with a no-reply notice.")}</span>
          <span>{text.length} / 4096</span>
        </div>

        {error && (
          <div className="sa-modal-error" style={{ marginTop: "0.5rem" }}>
            ⚠️ {error}
          </div>
        )}

        <div className="sa-modal-actions">
          <button type="button" className="sa-modal-btn" onClick={onClose} disabled={busy}>
            {t("sa.send_msg.cancel", "Cancel")}
          </button>
          <button
            type="button"
            className="sa-modal-btn primary"
            onClick={submit}
            disabled={busy || !text.trim()}
          >
            {busy ? `⏳ ${t("sa.send_msg.sending", "Sending…")}` : `📨 ${t("sa.send_msg.send", "Send")}`}
          </button>
        </div>
      </div>
    </div>
  );
}
