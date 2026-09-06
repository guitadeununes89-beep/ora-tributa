import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AssistedConsultation } from "./assisted-consultation";

const apiFetch = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("AssistedConsultation", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/products"
          ? jsonResponse([
              {
                id: "prod-1",
                internal_code: "PROD-1",
                description: "Produto sintético de teste",
                current_version: 1,
              },
            ])
          : jsonResponse([]),
      ));
  });

  it("presents the governed journey from product to reproducible history", async () => {
    render(<AssistedConsultation />);

    // The initial useEffect fetches products/catalogs and only then updates state; wait
    // for that real, observable consequence (the fetched product's option appearing)
    // instead of guessing at a microtask count. Without this, the update can land after
    // Vitest tears down this file's jsdom environment and throw "window is not defined"
    // — intermittent because it is a real race, not a flaky assertion.
    await screen.findByRole("option", { name: /PROD-1/ });

    const journey = screen.getByRole("navigation", { name: "Fluxo da consulta tributária" });
    for (const step of [
      "Produto",
      "Consulta IBS/CBS",
      "Informações da operação",
      "RT-IBSCBS-0003",
      "CST 200 · cClassTrib 200010",
      "Fundamento legal",
      "DecisionTrace",
      "Histórico reproduzível",
    ]) {
      expect(journey).toHaveTextContent(step);
    }
    expect(screen.getByLabelText("Produto cadastrado")).toBeRequired();
    expect(screen.getByRole("heading", { name: "Qual objeto será analisado?" }))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Produto\/Mercadoria/ })).toBeEnabled();
    expect(screen.getByRole("button", { name: /Serviço/ })).toBeDisabled();
    expect(screen.getByText("REGRA PILOTO REAL")).toBeInTheDocument();
    expect(screen.getByText("RT-IBSCBS-0003", { selector: ".rule-gate strong" }))
      .toBeInTheDocument();
  });
});
