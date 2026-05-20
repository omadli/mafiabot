/**
 * Vitest setup — runs once before every test file.
 *
 * Pulls in jest-dom's custom matchers (.toBeInTheDocument, .toHaveClass, …)
 * and ensures the i18next test mode is loaded so `t("…")` works without
 * a Suspense boundary.
 */
import "@testing-library/jest-dom/vitest";

import i18n from "@shared/i18n";

// jsdom defaults to en-US which the i18n detector would honour; force uz
// for deterministic test assertions.
await i18n.changeLanguage("uz");
