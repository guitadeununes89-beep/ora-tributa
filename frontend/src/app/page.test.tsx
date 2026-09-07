import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Home from "./page";

vi.mock("@/lib/api", () => ({
  apiFetch: () => Promise.resolve(new Response(JSON.stringify({
    metrics: {
      total_cclasstrib: 164,
      foundation_identified: 163,
      published: 4,
      executable_percentage: "2.44",
    },
    items: [
      { rules: [{ rule_code: "RT-IBSCBS-0003", status: "PUBLISHED" }] },
      { rules: [{ rule_code: "RT-IBSCBS-0004", status: "PUBLISHED" }] },
      { rules: [
        { rule_code: "RT-IBSCBS-0003", status: "PUBLISHED" },
        { rule_code: "RT-IBSCBS-0005", status: "PUBLISHED" },
      ] },
      { rules: [{ rule_code: "RT-IBSCBS-0007", status: "PUBLISHED" }] },
      { rules: [{ rule_code: "RT-IBSCBS-0008", status: "PUBLISHED" }] },
      { rules: [{ rule_code: "RT-IBSCBS-0002", status: "DRAFT" }] },
    ],
  }), { status: 200, headers: { "Content-Type": "application/json" } })),
}));

describe("Home", () => {
  it("comunica o catálogo nacional e a cobertura real sem exagerar nem defasar", async () => {
    render(<Home />);
    const status = screen.getByRole("status");
    expect(await screen.findByText("5 regras publicadas")).toBeInTheDocument();
    expect(status).toHaveTextContent("164");
    expect(status).toHaveTextContent("163 de 164");
    expect(status).toHaveTextContent("2,44%");
    expect(status).toHaveTextContent("4 de 164 cClassTrib");
    expect(status).toHaveTextContent("não são default de produção");
    expect(screen.getByRole("link", { name: /Cobertura normativa/ })).toHaveAttribute(
      "href", "/reforma-tributaria/cobertura",
    );
  });
});
