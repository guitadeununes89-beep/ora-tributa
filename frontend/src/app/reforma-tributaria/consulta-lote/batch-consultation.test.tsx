import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BatchConsultation } from "./batch-consultation";

const apiFetch = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
  API_URL: "http://localhost:8000/api/v1",
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function selectFile(input: HTMLElement, file: File) {
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  fireEvent.change(input);
}

const UPLOAD_RESPONSE = {
  batch: {
    batch_id: "batch-1",
    file_name: "lote.xlsx",
    file_hash: "a".repeat(64),
    status: "RECEIVED",
    row_count: 1,
    processed_count: 0,
    error_count: 0,
    truncated: false,
    max_rows: 500,
    created_at: "2026-09-09T10:00:00Z",
    completed_at: null,
  },
  unknown_headers: ["buyer.health_entity_status"],
  recognized_headers: ["ncm"],
  preview: [
    {
      row_number: 1,
      internal_code: "SKU-1",
      description: "Heparina e seus sais",
      ncm: "30019010",
      nbs: null,
      object_kind: "GOOD",
      processing_status: "PENDING",
      error_message: null,
      classification_status: null,
      cst: null,
      cclasstrib: null,
      tratamento: null,
      fundamento_legal: [],
      regra: null,
      fatos_faltantes: [],
      decision_trace: [],
      observacoes: null,
      evaluation_id: null,
    },
  ],
};

function detailWith(rows: unknown[], overrides: Record<string, unknown> = {}) {
  return {
    batch: {
      ...UPLOAD_RESPONSE.batch,
      status: "COMPLETED",
      processed_count: rows.length,
      error_count: 0,
      completed_at: "2026-09-09T10:01:00Z",
      ...overrides,
    },
    rows,
  };
}

async function uploadFile() {
  const input = screen.getByLabelText("Arquivo");
  selectFile(input, new File(["conteudo"], "lote.xlsx", { type: "application/octet-stream" }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar e validar" }));
  await screen.findByText("lote.xlsx");
}

describe("BatchConsultation", () => {
  afterEach(() => cleanup());
  beforeEach(() => {
    apiFetch.mockReset();
  });

  it("uploads a spreadsheet and shows the preview with unknown-header warnings", async () => {
    apiFetch.mockResolvedValue(jsonResponse(UPLOAD_RESPONSE));

    render(<BatchConsultation />);
    await uploadFile();

    expect(screen.getByText("1 linha(s) reconhecida(s)")).toBeInTheDocument();
    expect(screen.getByText(/buyer.health_entity_status/)).toBeInTheDocument();
    expect(screen.getByText("Heparina e seus sais")).toBeInTheDocument();

    const call = apiFetch.mock.calls.find((args: unknown[]) => args[0] === "/batch-classification/upload");
    expect(call).toBeDefined();
    const init = call![1] as { method: string; body: FormData };
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.body.get("file")).toBeInstanceOf(File);
  });

  it("shows an upload error message when the API rejects the file", async () => {
    apiFetch.mockResolvedValue(jsonResponse({ detail: "Arquivo excede o limite de bytes" }, 413));

    render(<BatchConsultation />);
    const input = screen.getByLabelText("Arquivo");
    selectFile(input, new File(["x"], "lote.xlsx"));
    fireEvent.click(screen.getByRole("button", { name: "Enviar e validar" }));

    await screen.findByText("Arquivo excede o limite de bytes");
  });

  it("processes the batch and shows a conclusive row's CST/cClassTrib and DecisionTrace", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/batch-classification/upload") return Promise.resolve(jsonResponse(UPLOAD_RESPONSE));
      return Promise.resolve(
        jsonResponse(
          detailWith([
            {
              ...UPLOAD_RESPONSE.preview[0],
              processing_status: "PROCESSED",
              classification_status: "CONCLUSIVO",
              cst: "200",
              cclasstrib: "200010",
              tratamento: "CST 200 / cClassTrib 200010",
              regra: { rule_code: "RT-IBSCBS-0005", version: "1" },
              fundamento_legal: [{ act_type: "LC", number: "214", year: 2025, device: "art. 146" }],
              decision_trace: [
                { sequence: 1, phase: "SELECTION", description: "Regra selecionada", outcome: "SELECTED" },
              ],
              observacoes: "Conclusivo via RT-IBSCBS-0005 (CST 200 / cClassTrib 200010).",
              evaluation_id: "eval-1",
            },
          ]),
        ),
      );
    });

    render(<BatchConsultation />);
    await uploadFile();
    fireEvent.click(screen.getByRole("button", { name: "3. Processar lote" }));

    await screen.findByText("1 processada(s) · 0 erro(s)");
    expect(screen.getAllByText("Conclusivo").length).toBeGreaterThan(0);
    expect(screen.getByText("CST 200")).toBeInTheDocument();
    expect(screen.getByText("cClassTrib 200010")).toBeInTheDocument();
    fireEvent.click(screen.getByText("DecisionTrace auditável"));
    expect(screen.getByText(/Regra selecionada/)).toBeInTheDocument();
  });

  it("filters the results grid by status", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/batch-classification/upload") return Promise.resolve(jsonResponse(UPLOAD_RESPONSE));
      return Promise.resolve(
        jsonResponse(
          detailWith([
            {
              ...UPLOAD_RESPONSE.preview[0],
              row_number: 1,
              processing_status: "PROCESSED",
              classification_status: "CONCLUSIVO",
              cst: "200",
              cclasstrib: "200010",
            },
            {
              ...UPLOAD_RESPONSE.preview[0],
              row_number: 2,
              ncm: "01012100",
              processing_status: "PROCESSED",
              classification_status: "SEM_COBERTURA_NORMATIVA",
              observacoes: "Sem cobertura normativa.",
            },
          ]),
        ),
      );
    });

    render(<BatchConsultation />);
    await uploadFile();
    fireEvent.click(screen.getByRole("button", { name: "3. Processar lote" }));
    await screen.findByText("2 processada(s) · 0 erro(s)");

    expect(screen.getByText("2 linha(s)")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "Status" }), {
      target: { value: "SEM_COBERTURA_NORMATIVA" },
    });

    expect(screen.getByText("1 linha(s)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Linha 2/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Linha 1/ })).not.toBeInTheDocument();
  });

  it("renders an export link pointing to the batch export endpoint", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/batch-classification/upload") return Promise.resolve(jsonResponse(UPLOAD_RESPONSE));
      return Promise.resolve(
        jsonResponse(
          detailWith(
            [
              {
                ...UPLOAD_RESPONSE.preview[0],
                processing_status: "ERROR",
                error_message: "NCM não encontrado no catálogo NCM publicado",
              },
            ],
            { processed_count: 0, error_count: 1 },
          ),
        ),
      );
    });

    render(<BatchConsultation />);
    await uploadFile();
    fireEvent.click(screen.getByRole("button", { name: "3. Processar lote" }));

    await screen.findByText("0 processada(s) · 1 erro(s)");
    const link = screen.getByRole("link", { name: "Exportar resultado (.xlsx)" });
    expect(link).toHaveAttribute("href", "http://localhost:8000/api/v1/batch-classification/batch-1/export");
    expect(screen.getByText("NCM não encontrado no catálogo NCM publicado")).toBeInTheDocument();
  });

  it("shows a row still awaiting processing distinctly from an error (Etapa 24)", async () => {
    // Regression test: while a batch is PROCESSING, rows the job has not
    // reached yet are `processing_status: "PENDING"` with no
    // classification_status - `rowStatusKey` must never collapse that into
    // "ERROR".
    apiFetch.mockImplementation((path: string) => {
      if (path === "/batch-classification/upload") return Promise.resolve(jsonResponse(UPLOAD_RESPONSE));
      if (path === "/batch-classification/batch-1/process") {
        return Promise.resolve(jsonResponse({ ...UPLOAD_RESPONSE.batch, status: "PROCESSING" }));
      }
      return Promise.resolve(
        jsonResponse(
          detailWith([UPLOAD_RESPONSE.preview[0]], {
            status: "PROCESSING",
            processed_count: 0,
            error_count: 0,
          }),
        ),
      );
    });

    render(<BatchConsultation />);
    await uploadFile();
    fireEvent.click(screen.getByRole("button", { name: "3. Processar lote" }));

    await screen.findByText(/Processando\.\.\. 0 de 1 linha/);
    const row = screen.getByRole("button", { name: /Linha 1/ });
    expect(row).toHaveTextContent("Aguardando processamento");
    expect(row.querySelector("small")).not.toHaveClass("status-error");
  });

  it("polls GET /{id} while PROCESSING and stops once the batch COMPLETED", async () => {
    vi.useFakeTimers();
    try {
      let detailCalls = 0;
      apiFetch.mockImplementation((path: string) => {
        if (path === "/batch-classification/upload") {
          return Promise.resolve(jsonResponse(UPLOAD_RESPONSE));
        }
        if (path === "/batch-classification/batch-1/process") {
          return Promise.resolve(jsonResponse({ ...UPLOAD_RESPONSE.batch, status: "PROCESSING" }));
        }
        if (path === "/batch-classification/batch-1") {
          detailCalls += 1;
          if (detailCalls === 1) {
            return Promise.resolve(
              jsonResponse(
                detailWith([UPLOAD_RESPONSE.preview[0]], {
                  status: "PROCESSING",
                  processed_count: 0,
                  error_count: 0,
                }),
              ),
            );
          }
          return Promise.resolve(
            jsonResponse(
              detailWith(
                [
                  {
                    ...UPLOAD_RESPONSE.preview[0],
                    processing_status: "PROCESSED",
                    classification_status: "CONCLUSIVO",
                    cst: "200",
                    cclasstrib: "200010",
                  },
                ],
                { status: "COMPLETED", processed_count: 1, error_count: 0 },
              ),
            ),
          );
        }
        return Promise.resolve(jsonResponse({}));
      });

      render(<BatchConsultation />);

      const input = screen.getByLabelText("Arquivo");
      selectFile(input, new File(["conteudo"], "lote.xlsx"));
      fireEvent.click(screen.getByRole("button", { name: "Enviar e validar" }));
      await vi.waitFor(() => expect(screen.getByText("lote.xlsx")).toBeInTheDocument());

      fireEvent.click(screen.getByRole("button", { name: "3. Processar lote" }));
      await vi.waitFor(() => expect(detailCalls).toBe(1));

      await vi.advanceTimersByTimeAsync(1000);
      await vi.waitFor(() => expect(screen.getByText("1 processada(s) · 0 erro(s)")).toBeInTheDocument());
      expect(screen.getByText("CST 200")).toBeInTheDocument();

      const callsAtCompletion = detailCalls;
      await vi.advanceTimersByTimeAsync(3000);
      expect(detailCalls).toBe(callsAtCompletion);
    } finally {
      vi.useRealTimers();
    }
  });
});
