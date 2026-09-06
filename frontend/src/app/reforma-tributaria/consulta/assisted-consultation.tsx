"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Product = {
  id: string;
  internal_code: string;
  description: string;
  current_version: number;
};
type Catalog = { id: string; version: string; status: string };
type RuleReference = {
  identity_id: string;
  rule_code: string;
  version_id: string;
  version: number;
  content_hash: string;
};
type LegalReference = {
  source_id: string;
  act_type: string;
  number: string;
  year: number;
  issuing_authority: string;
  device: string;
  official_uri: string | null;
};
type Result = {
  evaluation_id: string;
  evaluated_at: string;
  known_at: string;
  input_hash: string;
  engine_version: string;
  product_id: string | null;
  product_version_id: string | null;
  status: string;
  catalog_version_id: string;
  ruleset: { ruleset_id: string; version: string; content_hash: string };
  tax_candidates: {
    cst: string;
    cclasstrib: string | null;
    support: string;
    rule: RuleReference;
    missing_facts: string[];
  }[];
  official_candidates: {
    cst: string;
    cst_description: string;
    cclasstrib: string | null;
    cclasstrib_name: string | null;
    valid_from: string | null;
    valid_to: string | null;
  }[];
  missing_facts: string[];
  legal_references: LegalReference[];
  rules_evaluated: RuleReference[];
  decision_trace: {
    sequence: number;
    phase: string;
    description: string;
    outcome: string;
    details: Record<string, string>;
  }[];
};

const PILOT_RULESET = "IBSCBS-PILOT-001";
const JOURNEY = [
  "Produto",
  "Consulta IBS/CBS",
  "Informações da operação",
  "RT-IBSCBS-0003",
  "CST 200 · cClassTrib 200010",
  "Fundamento legal",
  "DecisionTrace",
  "Histórico reproduzível",
];

export function AssistedConsultation() {
  const params = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [productId, setProductId] = useState(params.get("product_id") ?? "");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const selectedProduct = products.find((product) => product.id === productId);

  useEffect(() => {
    void Promise.all([
      apiFetch("/products"),
      apiFetch("/taxonomy/ibs-cbs/catalogs?status=PUBLISHED"),
    ]).then(async ([productResponse, catalogResponse]) => {
      if (productResponse.ok) setProducts((await productResponse.json()) as Product[]);
      if (catalogResponse.ok) setCatalogs((await catalogResponse.json()) as Catalog[]);
    });
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const now = new Date().toISOString();
    const response = await apiFetch("/tax/ibs-cbs/classify", {
      method: "POST",
      body: JSON.stringify({
        evaluation_id: crypto.randomUUID(),
        ruleset_id: PILOT_RULESET,
        catalog_version_id: data.get("catalog_version_id"),
        product_id: data.get("product_id"),
        operation_date: data.get("operation_date"),
        evaluated_at: now,
        known_at: now,
        product_attributes: {
          "product.kind": data.get("product.kind"),
          "product.anvisa_registration_status": data.get("product.anvisa_registration_status"),
          "buyer.legal_nature": data.get("buyer.legal_nature"),
          "operation.buyer_is_acquirer": data.get("operation.buyer_is_acquirer"),
        },
      }),
    });
    if (!response.ok) {
      const problem = (await response.json()) as { detail?: string };
      setError(problem.detail ?? "Consulta indisponível.");
      setResult(null);
      return;
    }
    setResult((await response.json()) as Result);
    setError("");
  }

  return <section>
    <nav aria-label="Fluxo da consulta tributária" className="tax-journey">
      <ol>{JOURNEY.map((step, index) => <li key={step} className={result ? "journey-complete" : index < 4 ? "journey-current" : ""}>
        <span>{String(index + 1).padStart(2, "0")}</span>{step}
      </li>)}</ol>
    </nav>
    <div className="scope-warning">
      <strong>REGRA PILOTO REAL</strong> — escopo exclusivo da RT-IBSCBS-0003. A análise é
      determinística, usa o ruleset explícito {PILOT_RULESET} e não presume fatos ausentes.
    </div>
    <section className="object-kind-entry" aria-labelledby="object-kind-title">
      <header><div><span className="eyebrow">Ponto de entrada futuro</span>
        <h2 id="object-kind-title">Qual objeto será analisado?</h2></div>
        <small>Somente Produto/Mercadoria está disponível nesta etapa.</small></header>
      <div className="object-kind-grid">
        <button type="button" className="object-kind-active" aria-pressed="true"><strong>Produto/Mercadoria</strong><span>Cadastro versionado disponível</span></button>
        {["Serviço", "Direito", "Operação", "Importação", "Exportação", "Imóvel"].map((kind) =>
          <button type="button" disabled key={kind}><strong>{kind}</strong><small className="future-badge">Em desenvolvimento</small></button>)}
      </div>
    </section>
    <form className="consultation-form" onSubmit={submit}>
      <fieldset>
        <legend>1. Produto</legend>
        <label>Produto cadastrado<select name="product_id" required value={productId} onChange={(event) => setProductId(event.target.value)}>
          <option value="">Selecione um produto</option>
          {products.map((product) => <option key={product.id} value={product.id}>
            {product.internal_code} — {product.description}
          </option>)}
        </select></label>
        {products.length === 0 && <p className="form-help">Nenhum produto disponível. <Link href="/produtos/novo">Cadastre o primeiro produto</Link>.</p>}
        {selectedProduct && <p className="selected-context"><strong>{selectedProduct.internal_code}</strong> — {selectedProduct.description} · versão cadastral {selectedProduct.current_version}</p>}
      </fieldset>
      <fieldset>
        <legend>2. Consulta IBS/CBS e informações da operação</legend>
        <div className="inline-form compact-form">
          <label>Data da operação<input name="operation_date" type="date" required /></label>
          <label>Catálogo oficial publicado<select name="catalog_version_id" required defaultValue="">
            <option value="">Selecione</option>
            {catalogs.map((catalog) => <option key={catalog.id} value={catalog.id}>{catalog.version}</option>)}
          </select></label>
          <label>Ruleset piloto<input value={PILOT_RULESET} readOnly /></label>
          <label>Natureza do produto<select name="product.kind" required defaultValue="UNKNOWN">
            <option value="MEDICINE">Medicamento</option><option value="OTHER">Outro</option>
            <option value="UNKNOWN">Não informado</option>
          </select></label>
          <label>Registro sanitário<select name="product.anvisa_registration_status" required defaultValue="UNKNOWN">
            <option value="REGISTERED">Registrado</option><option value="NOT_REGISTERED">Não registrado</option>
            <option value="UNKNOWN">Não informado</option>
          </select></label>
          <label>Natureza jurídica do adquirente<select name="buyer.legal_nature" required defaultValue="UNKNOWN">
            <option value="DIRECT_PUBLIC_ADMINISTRATION_BODY">Administração pública direta</option>
            <option value="AUTARCHY">Autarquia</option><option value="PUBLIC_FOUNDATION">Fundação pública</option>
            <option value="PUBLIC_COMPANY">Empresa pública</option><option value="MIXED_CAPITAL_COMPANY">Sociedade de economia mista</option>
            <option value="PRIVATE_ENTITY">Entidade privada</option><option value="UNKNOWN">Não informada</option>
          </select></label>
          <label>Adquirente efetivo?<select name="operation.buyer_is_acquirer" required defaultValue="UNKNOWN">
            <option value="YES">Sim</option><option value="NO">Não</option><option value="UNKNOWN">Não informado</option>
          </select></label>
        </div>
      </fieldset>
      <div className="rule-gate">
        <span className="eyebrow">3. Regra avaliada</span>
        <strong>RT-IBSCBS-0003</strong>
        <small>O motor decidirá somente com os fatos informados e a versão publicada.</small>
      </div>
      <button type="submit">Executar consulta IBS/CBS</button>
    </form>
    {error && <p role="alert" className="curation-warning">{error}</p>}
    {result && <article className={`classification-result result-${result.status.toLowerCase()}`}>
      <span className="eyebrow">4. Resultado determinístico</span><h2>{result.status}</h2>
      <p><strong>Ruleset:</strong> {result.ruleset.ruleset_id} · versão {result.ruleset.version}</p>
      <p><strong>Fingerprint:</strong> <code>{result.ruleset.content_hash}</code></p>
      <p><strong>Catálogo:</strong> <code>{result.catalog_version_id}</code></p>
      {result.missing_facts.length > 0 && <div className="missing-facts"><h3>Fatos necessários ausentes</h3>
        <ul>{result.missing_facts.map((fact) => <li key={fact}>{fact}</li>)}</ul></div>}
      <h3>5. CST e cClassTrib</h3>{result.official_candidates.length === 0 ? <p>Nenhuma classificação aplicável.</p> :
        <div className="candidate-grid">{result.official_candidates.map((candidate) => <section className="candidate-card" key={`${candidate.cst}-${candidate.cclasstrib}`}>
          <strong>CST {candidate.cst}</strong><span>{candidate.cst_description}</span>
          {candidate.cclasstrib && <><strong>cClassTrib {candidate.cclasstrib}</strong><span>{candidate.cclasstrib_name}</span></>}
          <small>Vigência do catálogo: {candidate.valid_from ?? "não informada"} até {candidate.valid_to ?? "sem término registrado"}</small>
        </section>)}</div>}
      <section className="evidence-block"><h3>6. Fundamento legal</h3>
        {result.legal_references.length === 0 ? <p>Nenhum fundamento aplicado.</p> : <ul>{result.legal_references.map((source) =>
          <li key={source.source_id}>{source.act_type} {source.number}/{source.year}, {source.device} — {source.issuing_authority}
            {source.official_uri && <> · <a href={source.official_uri}>fonte oficial</a></>}</li>)}</ul>}
      </section>
      <section className="evidence-block"><h3>Versão da regra</h3>
        {result.rules_evaluated.map((rule) => <p key={rule.version_id}>{rule.rule_code} · versão {rule.version}<br />
          <small>ID: {rule.version_id} · hash: <code>{rule.content_hash}</code></small></p>)}
      </section>
      <details open><summary>7. DecisionTrace auditável</summary><ol>{result.decision_trace.map((step) =>
        <li key={step.sequence}><strong>{step.phase}</strong>: {step.description} — {step.outcome}
          {Object.keys(step.details).length > 0 && <ul>{Object.entries(step.details).map(([key, value]) =>
            <li key={key}>{key}: {value}</li>)}</ul>}</li>)}</ol></details>
      <section className="reproduction-record">
        <span className="eyebrow">8. Histórico reproduzível</span>
        <dl><dt>Avaliação</dt><dd><code>{result.evaluation_id}</code></dd>
          <dt>Produto</dt><dd><code>{result.product_id}</code></dd>
          <dt>Snapshot</dt><dd><code>{result.product_version_id}</code></dd>
          <dt>Input hash</dt><dd><code>{result.input_hash}</code></dd>
          <dt>Motor</dt><dd>{result.engine_version}</dd>
          <dt>Conhecido em</dt><dd>{new Date(result.known_at).toLocaleString("pt-BR")}</dd></dl>
        <p>Este registro preserva entrada, produto, regra, catálogo e ruleset necessários para reprodução determinística.</p>
      </section>
    </article>}
  </section>;
}
