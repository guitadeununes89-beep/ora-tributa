"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { API_URL, apiFetch } from "@/lib/api";

type ObjectKind = "GOOD" | "SERVICE" | "OTHER";
type ProcessingStatus = "PENDING" | "PROCESSED" | "ERROR";
type ClassificationStatus =
  | "CONCLUSIVO"
  | "POSSIVEIS_ENQUADRAMENTOS"
  | "NECESSITA_VALIDACAO"
  | "SEM_COBERTURA_NORMATIVA";
type BatchStatus = "RECEIVED" | "VALIDATED" | "PROCESSING" | "COMPLETED" | "FAILED";

type LegalReference = {
  act_type?: string;
  number?: string;
  year?: number;
  device?: string;
  issuing_authority?: string;
  official_uri?: string | null;
};

type DecisionStep = { sequence: number; phase: string; description: string; outcome: string };

type BatchRowResult = {
  row_number: number;
  internal_code: string | null;
  description: string | null;
  ncm: string | null;
  nbs: string | null;
  object_kind: ObjectKind | null;
  processing_status: ProcessingStatus;
  error_message: string | null;
  classification_status: ClassificationStatus | null;
  cst: string | null;
  cclasstrib: string | null;
  tratamento: string | null;
  fundamento_legal: LegalReference[];
  regra: { rule_code: string; version: string } | null;
  fatos_faltantes: string[];
  decision_trace: DecisionStep[];
  observacoes: string | null;
  evaluation_id: string | null;
};

type BatchSummary = {
  batch_id: string;
  file_name: string;
  file_hash: string;
  status: BatchStatus;
  row_count: number;
  processed_count: number;
  error_count: number;
  truncated: boolean;
  max_rows: number;
  created_at: string;
  completed_at: string | null;
};

type BatchUploadResponse = {
  batch: BatchSummary;
  unknown_headers: string[];
  recognized_headers: string[];
  preview: BatchRowResult[];
};

type BatchDetailResponse = {
  batch: BatchSummary;
  rows: BatchRowResult[];
};

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Aguardando processamento",
  CONCLUSIVO: "Conclusivo",
  POSSIVEIS_ENQUADRAMENTOS: "Possíveis enquadramentos",
  NECESSITA_VALIDACAO: "Necessita validação",
  SEM_COBERTURA_NORMATIVA: "Sem cobertura normativa",
  ERROR: "Erro na linha",
};

const POLL_INTERVAL_MS = 1000;

function rowStatusKey(row: BatchRowResult): string {
  if (row.processing_status === "ERROR") return "ERROR";
  if (row.processing_status === "PENDING") return "PENDING";
  return row.classification_status ?? "ERROR";
}

async function readProblemDetail(response: Response, fallback: string): Promise<string> {
  try {
    const problem = (await response.json()) as { detail?: string };
    return typeof problem.detail === "string" ? problem.detail : fallback;
  } catch {
    return fallback;
  }
}

export function BatchConsultation() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [upload, setUpload] = useState<BatchUploadResponse | null>(null);

  const [processing, setProcessing] = useState(false);
  const [processError, setProcessError] = useState("");
  const [detail, setDetail] = useState<BatchDetailResponse | null>(null);

  const [statusFilter, setStatusFilter] = useState("");
  const [selectedRowNumber, setSelectedRowNumber] = useState<number | null>(null);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function stopPolling() {
    if (pollIntervalRef.current !== null) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }

  // Never leave a timer running behind - on unmount, and whenever a new
  // file is uploaded while a previous batch was still being polled.
  useEffect(() => stopPolling, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function refreshDetail(batchId: string): Promise<BatchDetailResponse | null> {
    const response = await apiFetch(`/batch-classification/${batchId}`);
    if (!response.ok) return null;
    const data = (await response.json()) as BatchDetailResponse;
    setDetail(data);
    if (data.batch.status !== "PROCESSING") {
      stopPolling();
      setProcessing(false);
    }
    return data;
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    stopPolling();
    setUploading(true);
    setUploadError("");
    setUpload(null);
    setDetail(null);
    setSelectedRowNumber(null);
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiFetch("/batch-classification/upload", {
      method: "POST",
      body: formData,
    });
    setUploading(false);
    if (!response.ok) {
      setUploadError(await readProblemDetail(response, "Falha ao enviar a planilha."));
      return;
    }
    setUpload((await response.json()) as BatchUploadResponse);
  }

  async function handleProcess() {
    if (!upload) return;
    const batchId = upload.batch.batch_id;
    setProcessing(true);
    setProcessError("");
    // POST /process only enqueues the work and returns immediately
    // (Etapa 24) - the real result comes from polling GET below.
    const response = await apiFetch(`/batch-classification/${batchId}/process`, {
      method: "POST",
    });
    if (!response.ok) {
      setProcessing(false);
      setProcessError(await readProblemDetail(response, "Falha ao processar o lote."));
      return;
    }
    const initial = await refreshDetail(batchId);
    setSelectedRowNumber(initial?.rows[0]?.row_number ?? null);
    if (initial?.batch.status === "PROCESSING") {
      pollIntervalRef.current = setInterval(() => void refreshDetail(batchId), POLL_INTERVAL_MS);
    }
  }

  const filteredRows = useMemo(() => {
    const rows = detail?.rows ?? [];
    return statusFilter ? rows.filter((row) => rowStatusKey(row) === statusFilter) : rows;
  }, [detail, statusFilter]);
  const selectedRow = detail?.rows.find((row) => row.row_number === selectedRowNumber) ?? null;
  const exportUrl = detail
    ? `${API_URL}/batch-classification/${detail.batch.batch_id}/export`
    : null;
  const progressTotal = detail?.batch.row_count ?? 0;
  const progressDone = (detail?.batch.processed_count ?? 0) + (detail?.batch.error_count ?? 0);
  const progressPercent = progressTotal > 0 ? Math.round((progressDone / progressTotal) * 100) : 0;

  return (
    <section>
      <div className="scope-warning">
        <strong>CONSULTA EM LOTE — LIMITE INICIAL {upload?.batch.max_rows ?? 500} LINHAS</strong> —
        limite de configuração desta etapa, não capacidade definitiva do produto. Cada linha da
        planilha é avaliada pela mesma consulta unificada e descoberta já usadas na consulta
        individual — nenhum motor novo. Ausência de candidato nunca é apresentada como tributação
        geral; NCM/NBS isolados nunca determinam CST/cClassTrib automaticamente.
      </div>

      <section className="object-kind-entry" aria-labelledby="batch-upload-title">
        <header>
          <div>
            <span className="eyebrow">1. Upload</span>
            <h2 id="batch-upload-title">Enviar planilha (.xlsx ou .csv)</h2>
          </div>
          <small>Somente o hash do arquivo é retido; o conteúdo é descartado após a leitura.</small>
        </header>
        <form className="inline-form compact-form" onSubmit={(event) => void handleUpload(event)}>
          <label>
            Arquivo
            <input type="file" accept=".xlsx,.csv" onChange={handleFileChange} />
          </label>
          <button type="submit" disabled={!file || uploading} aria-busy={uploading}>
            {uploading ? "Enviando..." : "Enviar e validar"}
          </button>
        </form>
        {uploadError && (
          <p role="alert" className="curation-warning">
            {uploadError}
          </p>
        )}
      </section>

      {upload && (
        <section className="object-kind-entry" aria-labelledby="batch-preview-title">
          <header>
            <div>
              <span className="eyebrow">2. Prévia</span>
              <h2 id="batch-preview-title">{upload.batch.file_name}</h2>
            </div>
            <small>
              {upload.batch.row_count} linha(s) reconhecida(s)
              {upload.batch.truncated ? ` — truncado em ${upload.batch.max_rows}` : ""}
            </small>
          </header>
          {upload.unknown_headers.length > 0 && (
            <p className="curation-warning">
              Colunas não reconhecidas (viram fatos de contexto para o motor, nunca são
              descartadas): {upload.unknown_headers.join(", ")}
            </p>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Código interno</th>
                  <th>Descrição</th>
                  <th>NCM</th>
                  <th>NBS</th>
                </tr>
              </thead>
              <tbody>
                {upload.preview.map((row) => (
                  <tr key={row.row_number}>
                    <td>{row.row_number}</td>
                    <td>{row.internal_code ?? "—"}</td>
                    <td>{row.description ?? "—"}</td>
                    <td>{row.ncm ?? "—"}</td>
                    <td>{row.nbs ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {detail?.batch.status !== "PROCESSING" && (
            <button
              type="button"
              onClick={() => void handleProcess()}
              disabled={processing}
              aria-busy={processing}
            >
              {processing ? "Iniciando..." : "3. Processar lote"}
            </button>
          )}
          {detail?.batch.status === "PROCESSING" && (
            <div className="batch-progress" role="status" aria-live="polite">
              <p>
                Processando... {progressDone} de {progressTotal} linha(s)
              </p>
              <div
                className="coverage-progress"
                role="progressbar"
                aria-valuenow={progressPercent}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <span style={{ width: `${progressPercent}%` }} />
              </div>
            </div>
          )}
          {processError && (
            <p role="alert" className="curation-warning">
              {processError}
            </p>
          )}
        </section>
      )}

      {detail && (
        <section className="object-kind-entry" aria-labelledby="batch-results-title">
          <header>
            <div>
              <span className="eyebrow">4. Resultado</span>
              <h2 id="batch-results-title">
                {detail.batch.status === "PROCESSING"
                  ? "Processamento em andamento"
                  : `${detail.batch.processed_count} processada(s) · ${detail.batch.error_count} erro(s)`}
              </h2>
            </div>
            {exportUrl && detail.batch.status !== "PROCESSING" && (
              <a href={exportUrl} target="_blank" rel="noreferrer">
                Exportar resultado (.xlsx)
              </a>
            )}
          </header>
          <form className="coverage-filters" onSubmit={(event) => event.preventDefault()}>
            <label>
              Status
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">Todos</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <span>{filteredRows.length} linha(s)</span>
          </form>
          <div className="coverage-layout">
            <div className="coverage-list" aria-label="Linhas do lote">
              {filteredRows.map((row) => {
                const key = rowStatusKey(row);
                return (
                  <button
                    key={row.row_number}
                    type="button"
                    className={selectedRowNumber === row.row_number ? "selected" : ""}
                    onClick={() => setSelectedRowNumber(row.row_number)}
                  >
                    <span>
                      <strong>Linha {row.row_number}</strong> ·{" "}
                      {row.internal_code ?? row.ncm ?? row.nbs ?? row.description ?? "objeto não identificado"}
                    </span>
                    <small className={`coverage-status status-${key.toLowerCase()}`}>
                      {STATUS_LABELS[key] ?? key}
                    </small>
                  </button>
                );
              })}
            </div>
            {selectedRow && (
              <article
                className={`classification-result result-${rowStatusKey(selectedRow).toLowerCase()}`}
              >
                <span className="eyebrow">Linha {selectedRow.row_number}</span>
                <h2>{STATUS_LABELS[rowStatusKey(selectedRow)] ?? rowStatusKey(selectedRow)}</h2>
                {selectedRow.processing_status === "ERROR" && (
                  <p role="alert">{selectedRow.error_message}</p>
                )}
                {selectedRow.processing_status === "PENDING" && (
                  <p>Esta linha ainda não foi alcançada pelo processamento.</p>
                )}
                {selectedRow.processing_status === "PROCESSED" && (
                  <>
                    {selectedRow.fatos_faltantes.length > 0 && (
                      <div className="missing-facts">
                        <h3>Fatos necessários ausentes</h3>
                        <ul>
                          {selectedRow.fatos_faltantes.map((fact) => (
                            <li key={fact}>{fact}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <h3>CST e cClassTrib</h3>
                    {selectedRow.cst ? (
                      <div className="candidate-grid">
                        <section className="candidate-card">
                          <strong>CST {selectedRow.cst}</strong>
                          {selectedRow.cclasstrib && <span>cClassTrib {selectedRow.cclasstrib}</span>}
                          {selectedRow.regra && (
                            <small>
                              {selectedRow.regra.rule_code} v{selectedRow.regra.version}
                            </small>
                          )}
                        </section>
                      </div>
                    ) : (
                      <p>{selectedRow.observacoes ?? "Nenhuma classificação aplicável."}</p>
                    )}
                    {selectedRow.fundamento_legal.length > 0 && (
                      <section className="evidence-block">
                        <h3>Fundamento legal</h3>
                        <ul>
                          {selectedRow.fundamento_legal.map((source, index) => (
                            <li key={index}>
                              {source.act_type ?? ""} {source.number ?? ""}/{source.year ?? ""}
                              {source.device ? `, ${source.device}` : ""}
                            </li>
                          ))}
                        </ul>
                      </section>
                    )}
                    {selectedRow.observacoes && (
                      <p>
                        <small>{selectedRow.observacoes}</small>
                      </p>
                    )}
                    {selectedRow.decision_trace.length > 0 && (
                      <details>
                        <summary>DecisionTrace auditável</summary>
                        <ol>
                          {selectedRow.decision_trace.map((step) => (
                            <li key={step.sequence}>
                              <strong>{step.phase}</strong>: {step.description} — {step.outcome}
                            </li>
                          ))}
                        </ol>
                      </details>
                    )}
                  </>
                )}
              </article>
            )}
          </div>
        </section>
      )}
    </section>
  );
}
