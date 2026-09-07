import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssistedConsultationMedicamentos } from "./assisted-consultation-medicamentos";

const apiFetch = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

describe("AssistedConsultationMedicamentos", () => {
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

  it("defaults to RT-IBSCBS-0004 and exposes its own explicit ruleset", async () => {
    render(<AssistedConsultationMedicamentos />);

    await screen.findByRole("option", { name: "2026-06-23" });
    expect(screen.getByDisplayValue("IBSCBS-PILOT-0004-001")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^RT-IBSCBS-0004/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /RT-IBSCBS-0005/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(
      screen.getByRole("combobox", { name: "Correspondência ao Anexo XIV original" }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("NCM/SH verificada (evidência oficial, não inferida)"),
    ).toBeInTheDocument();
  });

  it("switches to RT-IBSCBS-0005's own fields and ruleset when selected", async () => {
    render(<AssistedConsultationMedicamentos />);
    await screen.findByRole("option", { name: "2026-06-23" });

    fireEvent.click(screen.getByRole("button", { name: /RT-IBSCBS-0005/ }));

    expect(screen.getByDisplayValue("IBSCBS-PILOT-0005-001")).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Situação do CEBAS" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("combobox", { name: "Correspondência ao Anexo XIV original" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("NCM/SH verificada (evidência oficial, não inferida)"),
    ).not.toBeInTheDocument();
  });
});
