/**
 * LangPicker — accessible custom dropdown for choosing a UI language.
 *
 * Replaces the native `<select>` because `<option>` cannot render SVG —
 * which means Windows users saw "UZ / RU / GB" letter pairs instead of
 * the flag emoji. This component renders SVG flags via the shared `Flag`
 * component and looks identical on every OS.
 *
 * Keyboard: Tab focuses the trigger, Enter/Space toggles, Esc closes,
 * Up/Down moves selection, Enter on a row commits.
 */
import {
  type CSSProperties,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import { Flag } from "./Flag";

export interface LangOption {
  code: string;
  label: string;
}

export const DEFAULT_LANG_OPTIONS: LangOption[] = [
  { code: "uz", label: "O'zbekcha" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

interface LangPickerProps {
  value: string;
  onChange: (code: string) => void;
  options?: LangOption[];
  className?: string;
  style?: CSSProperties;
  flagSize?: number;
  /** Compact variant — flag only, no label text. */
  iconOnly?: boolean;
}

export function LangPicker({
  value,
  onChange,
  options = DEFAULT_LANG_OPTIONS,
  className,
  style,
  flagSize = 14,
  iconOnly = false,
}: LangPickerProps) {
  const [open, setOpen] = useState(false);
  const [focusIdx, setFocusIdx] = useState(0);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const listId = useId();

  const current = options.find((o) => o.code === value) ?? options[0];

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  useEffect(() => {
    if (open) setFocusIdx(Math.max(0, options.findIndex((o) => o.code === value)));
  }, [open, options, value]);

  const onTriggerKey = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setOpen(true);
      }
    },
    [],
  );

  const onListKey = useCallback(
    (e: KeyboardEvent<HTMLUListElement>) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setOpen(false);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocusIdx((i) => (i + 1) % options.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocusIdx((i) => (i - 1 + options.length) % options.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        onChange(options[focusIdx].code);
        setOpen(false);
      }
    },
    [focusIdx, onChange, options],
  );

  return (
    <div
      ref={rootRef}
      className={className}
      style={{ position: "relative", display: "inline-block", ...style }}
    >
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={onTriggerKey}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          padding: iconOnly ? "4px 6px" : "4px 8px",
          border: "1px solid var(--border, #444)",
          borderRadius: 6,
          background: "var(--card-bg, #2a2a2a)",
          color: "var(--text, #e0e0e0)",
          cursor: "pointer",
          fontSize: "0.85rem",
          lineHeight: 1.2,
          minWidth: iconOnly ? undefined : 90,
        }}
      >
        <Flag lang={current.code} size={flagSize} />
        {!iconOnly && <span style={{ flex: 1, textAlign: "left" }}>{current.label}</span>}
        <span aria-hidden style={{ opacity: 0.6, fontSize: "0.75rem" }}>▾</span>
      </button>
      {open && (
        <ul
          role="listbox"
          id={listId}
          tabIndex={-1}
          autoFocus
          onKeyDown={onListKey}
          ref={(el) => el?.focus()}
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            right: 0,
            zIndex: 50,
            margin: 0,
            padding: 4,
            minWidth: iconOnly ? 140 : "100%",
            listStyle: "none",
            background: "var(--card-bg, #2a2a2a)",
            border: "1px solid var(--border, #444)",
            borderRadius: 6,
            boxShadow: "0 6px 16px rgba(0,0,0,0.3)",
          }}
        >
          {options.map((opt, idx) => {
            const isSelected = opt.code === value;
            const isFocused = idx === focusIdx;
            return (
              <li
                key={opt.code}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setFocusIdx(idx)}
                onClick={() => {
                  onChange(opt.code);
                  setOpen(false);
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "6px 8px",
                  borderRadius: 4,
                  cursor: "pointer",
                  background: isFocused ? "var(--hover, #3a3a3a)" : "transparent",
                  color: "var(--text, #e0e0e0)",
                  fontWeight: isSelected ? 600 : 400,
                  fontSize: "0.85rem",
                }}
              >
                <Flag lang={opt.code} size={flagSize} />
                <span style={{ flex: 1 }}>{opt.label}</span>
                {isSelected && <span aria-hidden style={{ color: "var(--accent, #4ade80)" }}>✓</span>}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
