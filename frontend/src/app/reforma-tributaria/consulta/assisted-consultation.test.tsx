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

describe("AssistedConsultation", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockImplementation(() => Promise.resolve(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ));
  });

  it("presents the governed journey from product to reproducible history", () => {
    render(<AssistedConsultation />);

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
