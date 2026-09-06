import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "./app-shell";

const apiFetch = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

function identity(permissions: string[]) {
  return new Response(JSON.stringify({
    display_name: "Usuário de teste",
    organization_name: "Organização fictícia",
    role: permissions.includes("MANAGE_MEMBERSHIP") ? "ADMIN" : "ANALYST",
    permissions,
  }), { status: 200, headers: { "Content-Type": "application/json" } });
}

describe("AppShell authorization-aware navigation", () => {
  beforeEach(() => apiFetch.mockReset());
  afterEach(() => cleanup());

  it("hides curation and membership management from a non-administrative profile", async () => {
    apiFetch.mockResolvedValue(identity(["READ", "RUN_EVALUATION"]));
    render(<AppShell><p>Conteúdo</p></AppShell>);

    await screen.findByText("Organização fictícia");
    expect(screen.queryByRole("link", { name: /Curadoria/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Usuários e Papéis/ })).not.toBeInTheDocument();
  });

  it("shows membership management only to a profile with its backend permission", async () => {
    apiFetch.mockResolvedValue(identity(["READ", "MANAGE_MEMBERSHIP"]));
    render(<AppShell><p>Conteúdo</p></AppShell>);

    await waitFor(() => expect(screen.getByRole("link", { name: /Usuários e Papéis/ }))
      .toBeInTheDocument());
    expect(screen.queryByRole("link", { name: /Curadoria/ })).not.toBeInTheDocument();
  });

  it("groups implemented and future reform modules without fictitious links", async () => {
    apiFetch.mockResolvedValue(identity(["READ"]));
    render(<AppShell><p>Conteúdo</p></AppShell>);

    await screen.findByText("Organização fictícia");
    expect(screen.getByRole("link", { name: /Classificação IBS\/CBS/ }))
      .toHaveAttribute("href", "/reforma-tributaria/classificacao");
    expect(screen.getByRole("link", { name: /Cobertura Normativa/ }))
      .toHaveAttribute("href", "/reforma-tributaria/cobertura");
    expect(screen.getByText("Imposto Seletivo").closest("a")).toBeNull();
    expect(screen.getByText("Transição 2026–2033").closest("a")).toBeNull();
    expect(screen.getByText("Simulação").closest("a")).toBeNull();
  });
});
