/**
 * Flag — inline SVG flag icon.
 *
 * Windows does not render regional-indicator emoji as flags (they fall back
 * to letter pairs like "UZ", "RU", "GB"). We ship the 3 supported locales
 * as tiny inline SVGs so the language pickers look identical everywhere.
 *
 * `lang` is the i18n locale code: "uz" | "ru" | "en". Unknown codes fall
 * back to a small uppercase chip so the UI never breaks.
 */
import type { CSSProperties } from "react";

type SupportedLang = "uz" | "ru" | "en";

interface FlagProps {
  lang: string;
  size?: number;
  style?: CSSProperties;
  title?: string;
}

const BASE_STYLE: CSSProperties = {
  display: "inline-block",
  verticalAlign: "middle",
  borderRadius: 2,
  boxShadow: "0 0 0 1px rgba(0,0,0,0.15)",
  flexShrink: 0,
};

function FlagUZ({ size, style, title }: { size: number; style?: CSSProperties; title?: string }) {
  // Uzbek flag — sky blue / white / green tricolor with thin red fimbriations,
  // crescent moon in the top-left. Stars omitted at icon scale.
  return (
    <svg
      viewBox="0 0 30 15"
      width={size * 2}
      height={size}
      style={{ ...BASE_STYLE, ...style }}
      aria-label={title || "Uzbekistan"}
    >
      <rect width="30" height="5" fill="#0099b5" />
      <rect y="5" width="30" height="5" fill="#fff" />
      <rect y="10" width="30" height="5" fill="#1eb53a" />
      <rect y="4.7" width="30" height="0.3" fill="#ce1126" />
      <rect y="10" width="30" height="0.3" fill="#ce1126" />
      <circle cx="5" cy="2.5" r="1.2" fill="#fff" />
      <circle cx="5.5" cy="2.5" r="1" fill="#0099b5" />
    </svg>
  );
}

function FlagRU({ size, style, title }: { size: number; style?: CSSProperties; title?: string }) {
  return (
    <svg
      viewBox="0 0 30 15"
      width={size * 2}
      height={size}
      style={{ ...BASE_STYLE, ...style }}
      aria-label={title || "Russia"}
    >
      <rect width="30" height="5" fill="#fff" />
      <rect y="5" width="30" height="5" fill="#0039a6" />
      <rect y="10" width="30" height="5" fill="#d52b1e" />
    </svg>
  );
}

function FlagGB({ size, style, title }: { size: number; style?: CSSProperties; title?: string }) {
  // Union Jack — blue field, white saltire (X), red saltire (X) shifted,
  // white cross (+), red cross (+). Drawn in viewBox 60x30 for clean ratios.
  return (
    <svg
      viewBox="0 0 60 30"
      width={size * 2}
      height={size}
      style={{ ...BASE_STYLE, ...style }}
      aria-label={title || "United Kingdom"}
    >
      <rect width="60" height="30" fill="#012169" />
      <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6" />
      <path d="M0,0 L60,30" stroke="#C8102E" strokeWidth="2" />
      <path d="M60,0 L0,30" stroke="#C8102E" strokeWidth="2" />
      <path d="M30,0 V30 M0,15 H60" stroke="#fff" strokeWidth="10" />
      <path d="M30,0 V30 M0,15 H60" stroke="#C8102E" strokeWidth="6" />
    </svg>
  );
}

const FLAG_COMPONENTS: Record<SupportedLang, typeof FlagUZ> = {
  uz: FlagUZ,
  ru: FlagRU,
  en: FlagGB,
};

export function Flag({ lang, size = 14, style, title }: FlagProps) {
  const Component = FLAG_COMPONENTS[lang as SupportedLang];
  if (!Component) {
    return (
      <span
        style={{
          ...BASE_STYLE,
          ...style,
          padding: "0 4px",
          fontSize: size * 0.7,
          background: "var(--card-bg, #2a2a2a)",
        }}
      >
        {lang.toUpperCase()}
      </span>
    );
  }
  return <Component size={size} style={style} title={title} />;
}

/** Render `<Flag /> Label` with consistent spacing — for `<option>`s embed
 *  the flag label string and use this in non-select contexts.
 */
export function FlagLabel({
  lang,
  label,
  size = 14,
}: {
  lang: string;
  label: string;
  size?: number;
}) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <Flag lang={lang} size={size} title={label} />
      {label}
    </span>
  );
}
