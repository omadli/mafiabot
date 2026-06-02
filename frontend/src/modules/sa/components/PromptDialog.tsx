/**
 * Lightweight reusable prompt modal used to replace native window.prompt()
 * inside the SuperAdmin pages (ban reason, grant diamonds, premium days,
 * block reason). Native prompts can't be localised, validated or styled
 * — this dialog provides all three with the same SendMessageDialog look.
 *
 * Mounts on both shells (`/admin/*` and `/webapp/sa/*`) — it only touches
 * shared CSS classes from `modules/sa/styles.css`.
 */

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

export interface PromptDialogProps {
  open: boolean;
  title: string;
  /** Optional intro / contextual line shown under the title. */
  subtitle?: string;
  label?: string;
  placeholder?: string;
  /** "number" forces numeric inputs; "text" keeps a free-form line. */
  inputType?: "text" | "number";
  /** Default value shown when the dialog opens. */
  initialValue?: string;
  /** Optional quick-pick buttons (number presets, reason snippets). */
  presets?: { label: string; value: string }[];
  /** Numeric only — clamps the parsed number. */
  min?: number;
  max?: number;
  /** Visual treatment for the confirm button — "primary" or "danger". */
  variant?: "primary" | "danger";
  confirmLabel: string;
  cancelLabel?: string;
  /** Async submit handler. Errors thrown here surface in the dialog. */
  onConfirm: (value: string) => Promise<void> | void;
  onClose: () => void;
}

export function PromptDialog({
  open,
  title,
  subtitle,
  label,
  placeholder,
  inputType = "text",
  initialValue = "",
  presets,
  min,
  max,
  variant = "primary",
  confirmLabel,
  cancelLabel,
  onConfirm,
  onClose,
}: PromptDialogProps) {
  const { t } = useTranslation();
  const [value, setValue] = useState(initialValue);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset every time the dialog is re-opened so each prompt starts clean.
  useEffect(() => {
    if (open) {
      setValue(initialValue);
      setError(null);
      // Slight delay so the panel renders before focus moves in.
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open, initialValue]);

  if (!open) return null;

  const validateNumber = (raw: string): { ok: boolean; n: number; msg?: string } => {
    const n = parseInt(raw.trim(), 10);
    if (Number.isNaN(n)) {
      return { ok: false, n: 0, msg: t("sa.prompt.err_not_number", "Enter a number") };
    }
    if (min !== undefined && n < min) {
      return { ok: false, n, msg: t("sa.prompt.err_min", "Min: {{min}}").replace("{{min}}", String(min)) };
    }
    if (max !== undefined && n > max) {
      return { ok: false, n, msg: t("sa.prompt.err_max", "Max: {{max}}").replace("{{max}}", String(max)) };
    }
    return { ok: true, n };
  };

  const submit = async () => {
    const trimmed = value.trim();
    if (!trimmed) {
      setError(t("sa.prompt.err_empty", "Field is empty"));
      return;
    }
    if (inputType === "number") {
      const v = validateNumber(trimmed);
      if (!v.ok) {
        setError(v.msg ?? null);
        return;
      }
    }
    setBusy(true);
    setError(null);
    try {
      await onConfirm(trimmed);
      onClose();
    } catch (e) {
      setError((e as Error).message || t("sa.prompt.err_failed", "Action failed"));
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
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="sa-modal-panel">
        <h3 style={{ margin: "0 0 0.25rem" }}>{title}</h3>
        {subtitle && (
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: 0 }}>
            {subtitle}
          </p>
        )}

        <div className="sa-prompt-field">
          {label && <label>{label}</label>}
          <input
            ref={inputRef}
            type={inputType}
            inputMode={inputType === "number" ? "numeric" : undefined}
            placeholder={placeholder}
            value={value}
            min={min}
            max={max}
            disabled={busy}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
              if (e.key === "Escape") onClose();
            }}
          />
          {presets && presets.length > 0 && (
            <div className="preset-row">
              {presets.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setValue(p.value)}
                  disabled={busy}
                >
                  {p.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div className="sa-modal-error" style={{ marginTop: "0.5rem" }}>
            ⚠️ {error}
          </div>
        )}

        <div className="sa-modal-actions">
          <button
            type="button"
            className="sa-modal-btn"
            onClick={onClose}
            disabled={busy}
          >
            {cancelLabel ?? t("sa.send_msg.cancel", "Cancel")}
          </button>
          <button
            type="button"
            className={`sa-modal-btn ${variant === "danger" ? "danger" : "primary"}`}
            style={
              variant === "danger"
                ? { background: "#c0392b", color: "#fff", borderColor: "transparent" }
                : undefined
            }
            onClick={submit}
            disabled={busy || !value.trim()}
          >
            {busy ? `⏳ ${t("sa.prompt.working", "Working…")}` : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
