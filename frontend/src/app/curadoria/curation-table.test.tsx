import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CurationTable } from "./curation-table";

describe("CurationTable", () => {
  it("exibe lifecycle e rastreabilidade de uma regra sintética", () => {
    render(<CurationTable versions={[{
      id: "TEST-RULE-001-V1", identity_code: "TEST-RULE-001", version: 1,
      lifecycle_status: "PUBLISHED", valid_from: "2000-01-01", valid_to: "2100-01-01",
      legal_source_id: "TEST-SOURCE-001", content_hash: "a".repeat(64),
      published_at: "2040-01-04T12:00:00Z", rulesets: ["TEST-RULESET-001"],
    }]} />);
    expect(screen.getByText("PUBLISHED")).toBeInTheDocument();
    expect(screen.getByText("TEST-SOURCE-001")).toBeInTheDocument();
    expect(screen.getByText("TEST-RULESET-001")).toBeInTheDocument();
  });
});

