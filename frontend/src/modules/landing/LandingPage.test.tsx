import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { LandingPage } from "./LandingPage";

vi.mock("@shared/api/client", () => ({
  api: { get: vi.fn().mockResolvedValue({ data: { items: [] } }) },
}));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("LandingPage", () => {
  it("renders hero title", () => {
    renderPage();
    // Title "MAFIA" appears twice (nav + hero), so use getAllByText
    expect(screen.getAllByText(/MAFIA/i).length).toBeGreaterThan(0);
  });

  it("renders admin link in nav", () => {
    renderPage();
    // "Admin panel" appears in nav AND footer — match all and assert >= 1
    const adminLinks = screen.getAllByText(/admin panel/i);
    expect(adminLinks.length).toBeGreaterThan(0);
  });

  it("renders main CTA to add the bot to a group", () => {
    renderPage();
    const ctas = screen.getAllByRole("link", { name: /guruhga qo'sh/i });
    expect(ctas[0]).toHaveAttribute("href", expect.stringContaining("t.me/MafGameUzBot"));
  });

  it("renders three team columns (civilians/mafia/singletons)", () => {
    renderPage();
    // headings come from i18n; check for landing.team_* equivalents
    expect(screen.getAllByText(/tinch aholilar/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/mafiya tomoni/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/singletonlar/i).length).toBeGreaterThan(0);
  });
});
