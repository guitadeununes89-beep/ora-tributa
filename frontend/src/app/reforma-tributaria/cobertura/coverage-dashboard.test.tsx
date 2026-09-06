import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CoverageDashboard } from "./coverage-dashboard";

vi.mock("@/lib/api", () => ({
  apiFetch: () => Promise.resolve(new Response(JSON.stringify({
    catalog: { version: "2026-06-23", version_id: "catalog", technical_document: "IT",
      artifact_hash: "a".repeat(64), official_url: "https://example.invalid" },
    metrics: { total_cclasstrib: 164, cataloged: 164, foundation_identified: 163, mapped: 163,
      catalog_only: 1, legal_mapping_required: 159, draft_specification: 3,
      ready_for_review: 1,
      legal_review: 0, approved: 0, implemented: 0, published: 1, blocked: 0,
      executable: 1, executable_percentage: "0.61" },
    families: [{ name: "Padrão", total_cclasstrib: 61, cataloged: 61,
      foundation_identified: 60, mapped: 60, catalog_only: 1, legal_mapping_required: 53,
      draft_specification: 6, legal_review: 0, approved: 0, implemented: 0,
      ready_for_review: 1,
      published: 1, blocked: 0, executable: 1, executable_percentage: "1.64" }],
    items: [], disclaimer: "cClassTrib is not a TaxRule",
  }), { status: 200, headers: { "Content-Type": "application/json" } })),
}));

describe("CoverageDashboard", () => {
  it("shows the real denominator and does not inflate executable coverage", async () => {
    render(<CoverageDashboard />);
    expect(await screen.findByText("0.61%")).toBeInTheDocument();
    expect(screen.getByText("1 de 164 cClassTrib possuem ao menos uma regra publicada."))
      .toBeInTheDocument();
    expect(screen.getByText("163")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cobertura por tipo de alíquota" }))
      .toBeInTheDocument();
    expect(screen.getByText("Padrão")).toBeInTheDocument();
    expect(screen.getByText(/não pressupõe relação 1:1/)).toBeInTheDocument();
    expect(screen.getAllByText(/Pronto para revisão/).length).toBeGreaterThan(0);
  });
});
