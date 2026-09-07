"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";

type Metrics = {
  total_cclasstrib: number; cataloged: number; foundation_identified: number;
  mapped: number;
  catalog_only: number; legal_mapping_required: number; draft_specification: number;
  ready_for_review: number;
  legal_review: number; approved: number; implemented: number; published: number;
  blocked: number; executable: number; executable_percentage: string;
};
type Family = Metrics & { name: string };
type Specification = { rule_id: string; version: number; title: string; status: string;
  legal_device: string; effective_from: string; effective_to: string | null };
type Rule = { rule_code: string; version: number; status: string; rule_version_id: string;
  legal_device: string; valid_from: string; valid_to: string | null; content_hash: string;
  queryable_rulesets: string[] };
type History = { catalog_version: string; catalog_version_id: string; name: string;
  official_description: string; valid_from: string | null; valid_to: string | null;
  updated_on: string | null; artifact_hash: string };
type CoverageItem = { cst: string; cst_description: string | null; cclasstrib: string;
  name: string; official_description: string; legal_device: string | null;
  official_url: string; valid_from: string | null; valid_to: string | null;
  indicators: Record<string, unknown>; catalog_version: string; catalog_version_id: string;
  coverage_status: string; foundation_identified: boolean; specifications: Specification[];
  review_readiness: string;
  rules: Rule[]; blockers: string[]; coverage_caveat: string | null; history?: History[] };
type Coverage = { catalog: { version: string; version_id: string; technical_document: string;
  artifact_hash: string; official_url: string }; metrics: Metrics; families: Family[]; items: CoverageItem[];
  disclaimer: string };

// Roteamento manual, temporário: cada ruleset publicado precisa apontar para a tela de
// consulta que sabe perguntar seus fatos. Cresce/atualiza junto com a cobertura (3/164 hoje);
// um ruleset sem entrada aqui simplesmente não ganha o link "Consultar" — nunca inventamos um.
const RULESET_CONSULTATION_LINKS: Record<string, string> = {
  "IBSCBS-PILOT-001": "/reforma-tributaria/consulta",
  "IBSCBS-ZFM-0007-PILOT-001": "/reforma-tributaria/consulta-zfm",
  "IBSCBS-ZFM-0008-PILOT-001": "/reforma-tributaria/consulta-zfm",
  "IBSCBS-PILOT-0004-001": "/reforma-tributaria/consulta-medicamentos",
  "IBSCBS-PILOT-0005-001": "/reforma-tributaria/consulta-medicamentos",
};

const STATUS_LABELS: Record<string, string> = {
  CATALOG_ONLY: "Somente catálogo", LEGAL_MAPPING_REQUIRED: "Mapeamento jurídico necessário",
  DRAFT_SPECIFICATION: "Especificação DRAFT", LEGAL_REVIEW: "Revisão jurídica",
  APPROVED: "Aprovado", IMPLEMENTED: "Implementado", PUBLISHED: "Publicado",
  BLOCKED_EXTERNAL_SOURCE: "Bloqueado por fonte externa",
};

export function CoverageDashboard() {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [selected, setSelected] = useState<CoverageItem | null>(null);
  const [query, setQuery] = useState(""); const [status, setStatus] = useState("");
  const [cst, setCst] = useState(""); const [error, setError] = useState(false);
  useEffect(() => { void apiFetch("/taxonomy/ibs-cbs/coverage").then(async (response) => {
    if (!response.ok) throw new Error("coverage unavailable");
    const data = await response.json() as Coverage; setCoverage(data); setSelected(data.items[0] ?? null);
  }).catch(() => setError(true)); }, []);
  const items = useMemo(() => (coverage?.items ?? []).filter((item) => {
    const term = query.trim().toLocaleLowerCase("pt-BR");
    return (!term || `${item.cclasstrib} ${item.name} ${item.official_description}`.toLocaleLowerCase("pt-BR").includes(term))
      && (!status || item.coverage_status === status) && (!cst || item.cst === cst);
  }), [coverage, query, status, cst]);
  async function select(item: CoverageItem) {
    setSelected(item); const response = await apiFetch(`/taxonomy/ibs-cbs/coverage/${item.cclasstrib}`);
    if (response.ok) setSelected(await response.json() as CoverageItem);
  }
  function filter(event: FormEvent) { event.preventDefault(); }
  if (error) return <p role="alert" className="curation-warning">Cobertura indisponível para esta sessão.</p>;
  if (!coverage) return <p>Carregando cobertura governada...</p>;
  const metricCards = [
    ["Catálogo oficial", coverage.metrics.total_cclasstrib],
    ["Mapeamento jurídico", coverage.metrics.mapped],
    ["Especificação DRAFT", coverage.metrics.draft_specification],
    ["Pronto para revisão", coverage.metrics.ready_for_review],
    ["Bloqueados", coverage.metrics.blocked], ["Aprovados", coverage.metrics.approved],
    ["Publicados", coverage.metrics.published],
  ] as const;
  return <section className="coverage-dashboard">
    <section className="coverage-hero" aria-label="Resumo da cobertura">
      <div><span className="eyebrow">Cobertura executável</span><strong>{coverage.metrics.executable_percentage}%</strong>
        <p>{coverage.metrics.executable} de {coverage.metrics.total_cclasstrib} cClassTrib possuem ao menos uma regra publicada.</p></div>
      <div className="coverage-progress" role="progressbar" aria-valuenow={Number(coverage.metrics.executable_percentage)} aria-valuemin={0} aria-valuemax={100}>
        <span style={{ width: `${coverage.metrics.executable_percentage}%` }} /></div>
      <small>{coverage.disclaimer}</small>
    </section>
    <div className="coverage-metrics">{metricCards.map(([label, value]) => <article key={label}>
      <span>{label}</span><strong>{value}</strong></article>)}</div>
    <section className="coverage-families" aria-labelledby="coverage-families-title">
      <header><div><span className="eyebrow">Visão por família oficial</span>
        <h2 id="coverage-families-title">Cobertura por tipo de alíquota</h2></div>
        <small>Contagem por cClassTrib distinto — não por quantidade de regras.</small></header>
      <div className="family-table-wrap"><table><thead><tr><th>Família</th><th>Total</th><th>Mapeados</th>
        <th>DRAFT</th><th>Prontos para revisão</th><th>Bloqueados</th><th>Aprovados</th><th>Publicados</th><th>Cobertura executável</th>
      </tr></thead><tbody>{coverage.families.map((family) => <tr key={family.name}>
        <td><strong>{family.name}</strong></td><td>{family.total_cclasstrib}</td><td>{family.mapped}</td>
        <td>{family.draft_specification}</td><td>{family.ready_for_review}</td><td>{family.blocked}</td>
        <td>{family.approved}</td><td>{family.published}</td><td><strong>{family.executable_percentage}%</strong><small>{family.executable}/{family.total_cclasstrib}</small></td>
      </tr>)}</tbody></table></div>
      <p className="family-caveat">Uma família e um cClassTrib podem exigir várias regras jurídicas.
        Esta visão não pressupõe relação 1:1.</p>
    </section>
    <aside className="source-card"><strong>Snapshot {coverage.catalog.version}</strong> · {coverage.catalog.technical_document}<br />
      <small>ID {coverage.catalog.version_id} · SHA-256 <code>{coverage.catalog.artifact_hash}</code></small></aside>
    <form className="coverage-filters" onSubmit={filter}>
      <label>Buscar código ou descrição<input value={query} onChange={(event) => setQuery(event.target.value)} /></label>
      <label>CST<input inputMode="numeric" pattern="[0-9]{3}" value={cst} onChange={(event) => setCst(event.target.value)} /></label>
      <label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Todos</option>
        {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <span>{items.length} código(s)</span>
    </form>
    <div className="coverage-layout">
      <div className="coverage-list" aria-label="cClassTrib do catálogo nacional">{items.map((item) => <button
        key={item.cclasstrib} type="button" onClick={() => void select(item)} className={selected?.cclasstrib === item.cclasstrib ? "selected" : ""}>
        <span><strong>{item.cclasstrib}</strong> · CST {item.cst}</span><span>{item.name}</span>
        <small className={`coverage-status status-${item.coverage_status.toLowerCase()}`}>{STATUS_LABELS[item.coverage_status]}</small>
      </button>)}</div>
      {selected && <article className="coverage-detail" aria-live="polite">
        <span className={`coverage-status status-${selected.coverage_status.toLowerCase()}`}>{STATUS_LABELS[selected.coverage_status]}</span>
        {selected.review_readiness === "READY_FOR_HUMAN_REVIEW" && <span className="coverage-status status-legal_review">Pronto para revisão humana</span>}
        {selected.review_readiness === "BLOCKED" && <span className="coverage-status status-blocked_external_source">Bloqueado</span>}
        <h2>{selected.cclasstrib} — {selected.name}</h2><p><strong>CST {selected.cst}:</strong> {selected.cst_description}</p>
        <p>{selected.official_description}</p><dl><dt>Dispositivo oficial</dt><dd>{selected.legal_device ?? "Não estruturado no snapshot"}</dd>
          <dt>Vigência</dt><dd>{selected.valid_from ?? "não informada"} → {selected.valid_to ?? "aberta"}</dd>
          <dt>Catálogo</dt><dd>{selected.catalog_version}</dd></dl>
        <a href={selected.official_url} target="_blank" rel="noreferrer">Abrir fonte oficial</a>
        {selected.coverage_caveat && <p className="curation-warning">{selected.coverage_caveat}</p>}
        <h3>Especificações associadas</h3>{selected.specifications.length ? <ul>{selected.specifications.map((spec) => <li key={spec.rule_id}>
          <strong>{spec.rule_id}</strong> v{spec.version} · {spec.status}<br /><small>{spec.legal_device}</small></li>)}</ul> : <p>Nenhuma especificação jurídica.</p>}
        <h3>Regras associadas</h3>{selected.rules.length ? <ul>{selected.rules.map((rule) => <li key={rule.rule_version_id}>
          <strong>{rule.rule_code}</strong> v{rule.version} · {rule.status}
          {rule.queryable_rulesets.map((rulesetId) => {
            const href = RULESET_CONSULTATION_LINKS[rulesetId];
            return href ? <a key={rulesetId} className="coverage-consult-link" href={href}>
              Consultar via {rulesetId} →</a> : null;
          })}</li>)}</ul> : <p>Nenhuma regra executável.</p>}
        {selected.blockers.length > 0 && <><h3>Bloqueadores explícitos</h3><ul>{selected.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul></>}
        <details><summary>Indicadores oficiais</summary><pre>{JSON.stringify(selected.indicators, null, 2)}</pre></details>
        <h3>Histórico da tabela</h3>{selected.history?.length ? <div className="coverage-history">{selected.history.map((entry) => <section key={entry.catalog_version_id}>
          <strong>{entry.catalog_version}</strong><span>{entry.name}</span><small>SHA-256 {entry.artifact_hash}</small></section>)}</div> : <p>Selecione o código para carregar o histórico.</p>}
      </article>}
    </div>
  </section>;
}
