import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { RoleConfigsPage } from "./RoleConfigsPage";
import { SaProvider } from "../context";

// `superAdminApi.roleConfigs` is the auth-aware client the unified page
// uses. Mock it directly rather than the legacy `adminApi` — the test
// doesn't care which backend prefix the dispatcher would pick.
vi.mock("@shared/api/superAdmin", async () => {
  const actual = await vi.importActual<object>("@shared/api/superAdmin");
  return {
    ...actual,
    superAdminApi: {
      roleConfigs: vi.fn().mockResolvedValue({
        items: [
          {
            role: "citizen", team: "civilians",
            name_uz: "Tinch aholi", name_ru: "Мирный житель", name_en: "Civilian",
            static_emoji: "👨🏼", custom_emoji_id: "", order_idx: 10,
            updated_at: null, updated_by_tg_id: null,
          },
          {
            role: "don", team: "mafia",
            name_uz: "Don", name_ru: "Дон", name_en: "Don",
            static_emoji: "🤵🏻", custom_emoji_id: "", order_idx: 110,
            updated_at: null, updated_by_tg_id: null,
          },
          {
            role: "snitch", team: "singletons",
            name_uz: "Sotqin", name_ru: "Предатель", name_en: "Snitch",
            static_emoji: "🤓", custom_emoji_id: "5370856771151730818", order_idx: 270,
            updated_at: null, updated_by_tg_id: null,
          },
        ],
      }),
      updateRoleConfig: vi.fn(),
    },
  };
});

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  // The unified page reads `surface` from `useSa()`; mount under the
  // admin surface so the test exercises the desktop table layout.
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SaProvider basePath="/admin" surface="admin">
          <RoleConfigsPage />
        </SaProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RoleConfigsPage", () => {
  it("renders the title and team sections", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText(/tinch aholilar/i).length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText(/mafiya tomoni/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/singletonlar/i).length).toBeGreaterThan(0);
  });

  it("renders each role row with its slug + name", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("citizen")).toBeInTheDocument();
    });
    expect(screen.getByText("don")).toBeInTheDocument();
    expect(screen.getByText("snitch")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Tinch aholi")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Sotqin")).toBeInTheDocument();
  });

  it("marks the row with a star when a custom_emoji_id is set", async () => {
    renderPage();
    await waitFor(() => {
      // Star appears next to roles with custom_emoji_id
      const stars = screen.getAllByText("★");
      expect(stars.length).toBeGreaterThan(0);
    });
  });
});
