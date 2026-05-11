/**
 * Minimal i18n hook — backed by localStorage + Telegram language_code fallback.
 *
 * Will be replaced by react-i18next in Phase 3, but this lets Phase 2 SuperAdmin
 * UI ship with proper localization right now.
 */

import { useCallback, useEffect, useState } from "react";

import { dictionaries, type Locale } from "./locales";

const LS_KEY = "mafia.locale";

function detectLocale(): Locale {
  // 1. LocalStorage override
  if (typeof window !== "undefined") {
    const stored = window.localStorage?.getItem(LS_KEY);
    if (stored === "uz" || stored === "ru" || stored === "en") {
      return stored;
    }

    // 2. Telegram WebApp user.language_code
    const tg = window.Telegram?.WebApp;
    const lang = tg?.initDataUnsafe?.user?.language_code;
    if (lang) {
      if (lang.startsWith("ru")) return "ru";
      if (lang.startsWith("en")) return "en";
      if (lang.startsWith("uz")) return "uz";
    }
  }

  return "uz";
}

export function useI18n() {
  const [locale, setLocaleState] = useState<Locale>(() => detectLocale());

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage?.setItem(LS_KEY, locale);
    }
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
  }, []);

  const t = useCallback(
    (key: string, fallback?: string): string => {
      return dictionaries[locale][key] ?? fallback ?? key;
    },
    [locale],
  );

  return { t, locale, setLocale };
}

// (Window.Telegram type is augmented in shared/api/client.ts)
