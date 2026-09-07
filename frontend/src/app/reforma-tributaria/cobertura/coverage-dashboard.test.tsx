import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CoverageDashboard } from "./coverage-dashboard";

const BASE_PAYLOAD = {
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
  disclaimer: "cClassTrib is not a TaxRule",
};

function mockApiFetch(items: unknown[]) {
  return () => Promise.resolve(new Response(JSON.stringify({ ...BASE_PAYLOAD, items }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  }));
}

vi.mock("@/lib/api", () => ({ apiFetch: vi.fn() }));

describe("CoverageDashboard", () => {
  afterEach(() => cleanup());

  it("shows the real denominator and does not inflate executable coverage", async () => {
    const { apiFetch } = await import("@/lib/api");
    vi.mocked(apiFetch).mockImplementation(mockApiFetch([]));
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

  it("links to the consultation screen for a queryable published ruleset", async () => {
    const { apiFetch } = await import("@/lib/api");
    vi.mocked(apiFetch).mockImplementation(mockApiFetch([{
      cst: "200", cst_description: "Fixture CST", cclasstrib: "200022", name: "Fixture item",
      official_description: "Official fixture description", legal_device: "Art. 445",
      official_url: "https://example.invalid/official", valid_from: "2026-01-01", valid_to: null,
      indicators: {}, catalog_version: "2026-06-23", catalog_version_id: "catalog",
      coverage_status: "PUBLISHED", foundation_identified: true, review_readiness: "NOT_APPLICABLE",
      specifications: [], blockers: [], coverage_caveat: null,
      rules: [{ rule_code: "RT-IBSCBS-0007", version: 1, status: "PUBLISHED",
        rule_version_id: "version-1", legal_device: "Art. 445", valid_from: "2026-01-01",
        valid_to: null, content_hash: "b".repeat(64),
        queryable_rulesets: ["IBSCBS-ZFM-0007-PILOT-001"] }],
    }]));
    render(<CoverageDashboard />);

    const link = await screen.findByRole("link", {
      name: "Consultar via IBSCBS-ZFM-0007-PILOT-001 →",
    });
    expect(link).toHaveAttribute("href", "/reforma-tributaria/consulta-zfm");
  });

  it("shows no consultation link when the rule has no queryable ruleset", async () => {
    const { apiFetch } = await import("@/lib/api");
    vi.mocked(apiFetch).mockImplementation(mockApiFetch([{
      cst: "200", cst_description: "Fixture CST", cclasstrib: "200099", name: "Fixture item",
      official_description: "Official fixture description", legal_device: "Art. 1",
      official_url: "https://example.invalid/official", valid_from: "2026-01-01", valid_to: null,
      indicators: {}, catalog_version: "2026-06-23", catalog_version_id: "catalog",
      coverage_status: "PUBLISHED", foundation_identified: true, review_readiness: "NOT_APPLICABLE",
      specifications: [], blockers: [], coverage_caveat: null,
      rules: [{ rule_code: "RT-IBSCBS-9999", version: 1, status: "PUBLISHED",
        rule_version_id: "version-2", legal_device: "Art. 1", valid_from: "2026-01-01",
        valid_to: null, content_hash: "c".repeat(64), queryable_rulesets: [] }],
    }]));
    render(<CoverageDashboard />);

    await screen.findByText("RT-IBSCBS-9999");
    expect(screen.queryByRole("link", { name: /Consultar via/ })).not.toBeInTheDocument();
  });
});
