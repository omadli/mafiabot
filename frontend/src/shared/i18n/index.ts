/**
 * i18next bootstrap.
 *
 * Resource bundles ship inline (no async loading) — keeps the WebApp boot fast
 * and avoids a flash of untranslated strings.
 *
 * Locale detection priority:
 *   1. localStorage "mafia.locale"  (user-chosen override)
 *   2. Telegram WebApp user.language_code
 *   3. Browser navigator.language
 *   4. "uz" (default)
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uz from "./locales/uz.json";

export const LOCALES = ["uz", "ru", "en"] as const;
export type Locale = (typeof LOCALES)[number];

const LS_KEY = "mafia.locale";

function detectLocale(): Locale {
  if (typeof window === "undefined") return "uz";

  const stored = window.localStorage?.getItem(LS_KEY);
  if (stored === "uz" || stored === "ru" || stored === "en") return stored;

  // Telegram WebApp
  const tg = (window as any).Telegram?.WebApp;
  const tgLang: string | undefined = tg?.initDataUnsafe?.user?.language_code;
  if (tgLang) {
    if (tgLang.startsWith("ru")) return "ru";
    if (tgLang.startsWith("en")) return "en";
    if (tgLang.startsWith("uz")) return "uz";
  }

  // Browser
  const nav = window.navigator?.language;
  if (nav) {
    if (nav.startsWith("ru")) return "ru";
    if (nav.startsWith("en")) return "en";
  }

  return "uz";
}

i18n
  .use(initReactI18next)
  .init({
    resources: {
      uz: { translation: uz },
      ru: { translation: ru },
      en: { translation: en },
    },
    lng: detectLocale(),
    fallbackLng: "uz",
    interpolation: {
      escapeValue: false, // React already escapes
    },
    returnNull: false,
  });

// Persist on language change
i18n.on("languageChanged", (lng) => {
  if (typeof window !== "undefined") {
    window.localStorage?.setItem(LS_KEY, lng);
    document.documentElement.lang = lng;
  }
});

export default i18n;
