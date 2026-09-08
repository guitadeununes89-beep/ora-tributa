import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { UnifiedConsultation } from "./unified-consultation";

const apiFetch = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

describe("UnifiedConsultation", () => {
  afterEach(() => cleanup());
  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify([{ id: "catalog-1", version: "2026-06-23", status: "PUBLISHED" }]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ));
  });

  it("starts with no rule selected and the submit button disabled", async () => {
    render(<UnifiedConsultation />);
    await screen.findByRole("option", { name: "2026-06-23" });

    for (const rule of [
      "RT-IBSCBS-0003",
      "RT-IBSCBS-0004",
      "RT-IBSCBS-0005",
      "RT-IBSCBS-0007",
      "RT-IBSCBS-0008",
    ]) {
      expect(screen.getByRole("button", { name: new RegExp(`^${rule}`) })).toHaveAttribute(
        "aria-pressed",
        "false",
      );
    }
    expect(screen.getByRole("button", { name: "Executar consulta unificada" })).toBeDisabled();
  });

  it("merges the field sets of every selected rule and dedupes shared facts", async () => {
    render(<UnifiedConsultation />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.click(screen.getByRole("button", { name: /^RT-IBSCBS-0007/ }));
    fireEvent.click(screen.getByRole("button", { name: /^RT-IBSCBS-0008/ }));

    expect(screen.getByRole("combobox", { name: "Origem da operação" })).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Estabelecimento do fornecedor" }),
    ).toBeInTheDocument();
    // "product.material_good_status" ("Natureza do objeto") is shared by both
    // RT-0007 and RT-0008 - it must render exactly once, not twice.
    expect(screen.getAllByRole("combobox", { name: "Natureza do objeto" })).toHaveLength(1);
    expect(screen.getByLabelText("Versão territorial governada da ZFM")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Executar consulta unificada" })).toBeEnabled();
  });

  it("shows the Anexo XIV window warning and NCM field only when RT-IBSCBS-0004 is selected", async () => {
    render(<UnifiedConsultation />);
    await screen.findByRole("option", { name: "2026-06-23" });

    expect(screen.queryByText(/Hipótese historicamente encerrada/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^RT-IBSCBS-0004/ }));

    expect(screen.getByText(/Hipótese historicamente encerrada/)).toBeInTheDocument();
    expect(
      screen.getByLabelText("NCM/SH verificada (evidência oficial, não inferida)"),
    ).toBeInTheDocument();
  });

  it("submits the composed ruleset_ids to /tax/ibs-cbs/classify-unified", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/taxonomy")) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: "catalog-1", version: "2026-06-23", status: "PUBLISHED" }]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      return Promise.resolve(
        new Response(
          JSON.stringify({
            status: "CONCLUSIVO",
            ruleset: { ruleset_id: "COMPOSED:A+B", version: "1.0.0-composed", content_hash: "x".repeat(64) },
            missing_facts: [],
            official_candidates: [],
            legal_references: [],
            decision_trace: [],
            evaluated_ruleset_ids: ["IBSCBS-ZFM-0007-PILOT-001", "IBSCBS-ZFM-0008-PILOT-001"],
            rule_candidacies: [
              {
                rule_code: "RT-IBSCBS-0007",
                status: "SUPPORTED",
                missing_facts: [],
                unconfirmed_scope_facts: [],
              },
              {
                rule_code: "RT-IBSCBS-0008",
                status: "SCOPE_UNCONFIRMED",
                missing_facts: [],
                unconfirmed_scope_facts: ["seller.establishment_zfm_relation"],
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    });

    render(<UnifiedConsultation />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.click(screen.getByRole("button", { name: /^RT-IBSCBS-0007/ }));
    fireEvent.click(screen.getByRole("button", { name: /^RT-IBSCBS-0008/ }));
    fireEvent.change(screen.getByLabelText("Data da operação"), {
      target: { value: "2026-06-01" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "Catálogo oficial publicado" }), {
      target: { value: "catalog-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Executar consulta unificada" }));

    await screen.findByText("CONCLUSIVO");
    const call = apiFetch.mock.calls.find(
      (args: unknown[]) => args[0] === "/tax/ibs-cbs/classify-unified",
    ) as [string, { body: string }] | undefined;
    expect(call).toBeDefined();
    const body = JSON.parse(call![1].body) as { ruleset_ids: string[] };
    expect(body.ruleset_ids).toEqual(["IBSCBS-ZFM-0007-PILOT-001", "IBSCBS-ZFM-0008-PILOT-001"]);
    expect(
      screen.getByText(/para considerar esta hipótese, confirme: seller.establishment_zfm_relation/),
    ).toBeInTheDocument();
  });
});
