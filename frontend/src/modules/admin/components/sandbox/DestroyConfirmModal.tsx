/**
 * Typed-confirm modal for destructive actions. The user must literally
 * type "DESTROY" before the action button un-disables — friction wall
 * against muscle-memory clicks.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface DestroyConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: string;
  matchWord?: string;
}

export function DestroyConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  message,
  matchWord = "DESTROY",
}: DestroyConfirmModalProps) {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const matches = input === matchWord;

  useEffect(() => {
    if (open) setInput("");
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div onClick={onClose} className="sb-modal-backdrop">
      <div onClick={(e) => e.stopPropagation()} className="admin-card sb-modal">
        <h3 style={{ marginTop: 0 }}>
          ⚠️ {title ?? t("admin.sandbox.destroy.title")}
        </h3>
        <p style={{ color: "var(--muted)", marginBottom: "1rem" }}>
          {message ?? t("admin.sandbox.destroy.message")}
        </p>
        <p style={{ marginBottom: "0.5rem" }}>
          {t("admin.sandbox.destroy.type_to_confirm", { word: matchWord })}
        </p>
        <input
          type="text"
          autoFocus
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="admin-input"
          placeholder={matchWord}
          style={{ width: "100%", marginBottom: "1rem" }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && matches) onConfirm();
          }}
        />
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
          <button type="button" className="admin-btn" onClick={onClose}>
            {t("admin.sandbox.destroy.cancel")}
          </button>
          <button
            type="button"
            className="admin-btn danger"
            onClick={onConfirm}
            disabled={!matches}
          >
            🗑 {t("admin.sandbox.destroy.confirm")}
          </button>
        </div>
      </div>
    </div>
  );
}
