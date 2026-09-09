"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
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
  CONCLUSIVO: "Conclusivo",
  POSSIVEIS_ENQUADRAMENTOS: "Possíveis enquadramentos",
  NECESSITA_VALIDACAO: "Necessita validação",
  SEM_COBERTURA_NORMATIVA: "Sem cobertura normativa",
  ERROR: "Erro na linha",
};

function rowStatusKey(row: BatchRowResult): string {
  return row.processing_status === "ERROR" ? "ERROR" : (row.classification_status ?? "ERROR");
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
  const [selectedRow, setSelectedRow] = useState<BatchRowResult | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadError("");
    setUpload(null);
    setDetail(null);
    setSelectedRow(null);
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
    setProcessing(true);
    setProcessError("");
    const response = await apiFetch(`/batch-classification/${upload.batch.batch_id}/process`, {
      method: "POST",
    });
    setProcessing(false);
    if (!response.ok) {
      setProcessError(await readProblemDetail(response, "Falha ao processar o lote."));
      return;
    }
    const data = (await response.json()) as BatchDetailResponse;
    setDetail(data);
    setSelectedRow(data.rows[0] ?? null);
  }

  const filteredRows = useMemo(() => {
    const rows = detail?.rows ?? [];
    return statusFilter ? rows.filter((row) => rowStatusKey(row) === statusFilter) : rows;
  }, [detail, statusFilter]);
  const exportUrl = detail
    ? `${API_URL}/batch-classification/${detail.batch.batch_id}/export`
    : null;

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
          <button
            type="button"
            onClick={() => void handleProcess()}
            disabled={processing}
            aria-busy={processing}
          >
            {processing ? "Processando lote..." : "3. Processar lote"}
          </button>
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
                {detail.batch.processed_count} processada(s) · {detail.batch.error_count} erro(s)
              </h2>
            </div>
            {exportUrl && (
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
                    className={selectedRow?.row_number === row.row_number ? "selected" : ""}
                    onClick={() => setSelectedRow(row)}
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
                {selectedRow.processing_status === "ERROR" ? (
                  <p role="alert">{selectedRow.error_message}</p>
                ) : (
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
