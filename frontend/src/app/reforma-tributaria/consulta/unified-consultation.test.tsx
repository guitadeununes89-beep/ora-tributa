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

  it("searches an object and shows a candidate suggestion that pre-selects rules", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/taxonomy")) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: "catalog-1", version: "2026-06-23", status: "PUBLISHED" }]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      if (path.startsWith("/catalog-discovery/search")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                origin: "NCM",
                code: "30019010",
                description: "Heparina e seus sais",
                level: 8,
                is_final: true,
                product_id: null,
                internal_code: null,
              },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (path.startsWith("/catalog-discovery/candidates")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              status: "CANDIDATE_WITH_RULE",
              family: {
                rule_codes: ["RT-IBSCBS-0004", "RT-IBSCBS-0005"],
                fundamento: "Capítulo 30 da NCM vigente",
                fonte: "https://portalunico.siscomex.gov.br/classif",
                versao: "NCM vigente em 08/09/2026",
                condicoes: "Ainda exige os fatos próprios de cada regra.",
              },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    });

    render(<UnifiedConsultation />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.change(screen.getByLabelText("Pesquisa"), { target: { value: "heparina" } });
    fireEvent.click(screen.getByRole("button", { name: "Pesquisar" }));

    await screen.findByText("Heparina e seus sais");
    fireEvent.click(screen.getByRole("button", { name: "Ver famílias de regras candidatas" }));

    await screen.findByText(/Candidato identificado para NCM 30019010/);
    expect(screen.getByText("Capítulo 30 da NCM vigente")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Usar esta sugestão" }));

    expect(screen.getByRole("button", { name: /^RT-IBSCBS-0004/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /^RT-IBSCBS-0005/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("shows no-coverage explicitly when discovery has no governed candidate", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/taxonomy")) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: "catalog-1", version: "2026-06-23", status: "PUBLISHED" }]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      if (path.startsWith("/catalog-discovery/search")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                origin: "NBS",
                code: "1.01",
                description: "Serviços de construção",
                level: 2,
                is_final: null,
                product_id: null,
                internal_code: null,
              },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (path.startsWith("/catalog-discovery/candidates")) {
        return Promise.resolve(
          new Response(JSON.stringify({ status: "NO_COVERAGE", family: null }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    });

    render(<UnifiedConsultation />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.change(screen.getByLabelText("Pesquisa"), { target: { value: "construção" } });
    fireEvent.click(screen.getByRole("button", { name: "Pesquisar" }));

    await screen.findByText("Serviços de construção");
    fireEvent.click(screen.getByRole("button", { name: "Ver famílias de regras candidatas" }));

    await screen.findByText(/Descoberta ainda sem cobertura suficiente para NBS 1.01/);
  });
});
