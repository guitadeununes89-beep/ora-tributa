import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssistedConsultationZfm } from "./assisted-consultation-zfm";

const apiFetch = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

const TERRITORIAL_AREA = {
  area_id: "TJA-ALC-TABATINGA",
  area_type: "ALC",
  official_name: "Área de Livre Comércio de Tabatinga",
  version: 1,
  version_id: "TJA-ALC-TABATINGA-V1",
  legal_device: "Lei nº 7.965/1989",
  criteria: { municipio_sede: "Tabatinga" },
  valid_from: "2026-01-01",
  valid_to: null,
};

function jsonResponse(body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

describe("AssistedConsultationZfm", () => {
  afterEach(() => cleanup());
  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/territory/areas")) return jsonResponse([TERRITORIAL_AREA]);
      return jsonResponse([{ id: "catalog-1", version: "2026-06-23", status: "PUBLISHED" }]);
    });
  });

  it("defaults to RT-IBSCBS-0007 and exposes its own explicit ruleset", async () => {
    render(<AssistedConsultationZfm />);

    await screen.findByRole("option", { name: "2026-06-23" });
    expect(screen.getByDisplayValue("IBSCBS-ZFM-0007-PILOT-001")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^RT-IBSCBS-0007/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /RT-IBSCBS-0008/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(
      screen.getByRole("combobox", { name: "Comprovação de internamento" }),
    ).toBeInTheDocument();
  });

  it("switches to RT-IBSCBS-0008's own fields and ruleset when selected", async () => {
    render(<AssistedConsultationZfm />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.click(screen.getByRole("button", { name: /RT-IBSCBS-0008/ }));

    expect(screen.getByDisplayValue("IBSCBS-ZFM-0008-PILOT-001")).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Estabelecimento do fornecedor" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("combobox", { name: "Comprovação de internamento" }),
    ).not.toBeInTheDocument();
  });

  it("shows a non-binding territorial hint when the municipio matches a governed area", async () => {
    render(<AssistedConsultationZfm />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.change(
      screen.getByLabelText("Município do estabelecimento (referência, opcional)"),
      { target: { value: "tabatinga" } },
    );

    expect(
      await screen.findByText(/Área de Livre Comércio de Tabatinga/),
    ).toBeInTheDocument();
    expect(screen.getByText(/referência informativa/)).toBeInTheDocument();
  });

  it("shows no territorial hint for a municipio absent from governed areas", async () => {
    render(<AssistedConsultationZfm />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.change(
      screen.getByLabelText("Município do estabelecimento (referência, opcional)"),
      { target: { value: "Curitiba" } },
    );

    expect(screen.queryByText(/referência informativa/)).not.toBeInTheDocument();
  });
});
