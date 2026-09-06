import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  SpecificationReadinessTable,
  type SpecificationReadiness,
} from "./specification-readiness";

function specification(
  readiness: SpecificationReadiness["readiness"],
): SpecificationReadiness {
  return {
    readiness,
    rule_id: "TEST-IBSCBS-0001",
    specification_version: 1,
    title: "Fixture sintética",
    status: readiness === "READY_FOR_IMPLEMENTATION" ? "APPROVED" : "DRAFT",
    responsible_party: "synthetic-author",
    legal_source_id: "TEST-SOURCE",
    catalog_version_id: "TEST-CATALOG",
    cst: "999",
    cclasstrib: "999999",
    effective_from: "2040-01-01",
    effective_to: "2041-01-01",
    issues:
      readiness === "NOT_READY"
        ? [{ code: "STATUS_NOT_APPROVED", path: "status", message: "Synthetic" }]
        : [],
    disclaimer: "Structural only",
  };
}

describe("SpecificationReadinessTable", () => {
  it("keeps READY and NOT_READY visually and textually distinct", () => {
    const ready = specification("READY_FOR_IMPLEMENTATION");
    const notReady = specification("NOT_READY");
    notReady.rule_id = "TEST-IBSCBS-0002";
    render(<SpecificationReadinessTable specifications={[ready, notReady]} />);
    expect(screen.getByText("READY_FOR_IMPLEMENTATION")).toHaveClass("status-ready");
    expect(screen.getByText("NOT_READY")).toHaveClass("status-not-ready");
    expect(screen.getByText(/STATUS_NOT_APPROVED/)).toBeInTheDocument();
  });

  it("does not imply that a pilot rule exists when the list is empty", () => {
    render(<SpecificationReadinessTable specifications={[]} />);
    expect(screen.getByText(/Nenhuma especificação jurídica real/)).toBeInTheDocument();
  });
});

