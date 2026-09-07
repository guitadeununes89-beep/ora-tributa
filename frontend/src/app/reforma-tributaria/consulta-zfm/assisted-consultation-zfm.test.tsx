import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssistedConsultationZfm } from "./assisted-consultation-zfm";

const apiFetch = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

describe("AssistedConsultationZfm", () => {
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
});
