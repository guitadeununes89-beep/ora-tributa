"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Catalog = { id: string; version: string; status: string };
type Scenario = "RT-IBSCBS-0004" | "RT-IBSCBS-0005";

type FieldOption = { value: string; label: string };
type FieldSpec = { name: string; label: string; options: FieldOption[] };

const UNKNOWN_OPTION: FieldOption = { value: "UNKNOWN", label: "Não informado" };

const RULESETS: Record<Scenario, { rulesetId: string; cclasstrib: string; title: string }> = {
  "RT-IBSCBS-0004": {
    rulesetId: "IBSCBS-PILOT-0004-001",
    cclasstrib: "200009",
    title: "Anexo XIV da redação original (janela histórica 01–13/01/2026)",
  },
  "RT-IBSCBS-0005": {
    rulesetId: "IBSCBS-PILOT-0005-001",
    cclasstrib: "200010",
    title: "Entidade de saúde imune com CEBAS e prestação ao SUS (art. 146, § 1º, II)",
  },
};

const FIELDS_0004: FieldSpec[] = [
  {
    name: "product.annex_xiv_match_status",
    label: "Correspondência ao Anexo XIV original",
    options: [
      { value: "MATCHED", label: "Confirmada" },
      { value: "NOT_MATCHED", label: "Não corresponde" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "normative.annex_xiv_version",
    label: "Versão normativa utilizada",
    options: [
      { value: "LC214_2025_ORIGINAL", label: "Publicação original da LC nº 214/2025" },
      UNKNOWN_OPTION,
    ],
  },
];

const FIELDS_0005: FieldSpec[] = [
  {
    name: "product.kind",
    label: "Natureza do produto",
    options: [
      { value: "MEDICINE", label: "Medicamento" },
      { value: "OTHER", label: "Outro" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.anvisa_registration_status",
    label: "Registro sanitário",
    options: [
      { value: "REGISTERED", label: "Registrado" },
      { value: "NOT_REGISTERED", label: "Não registrado" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.health_entity_status",
    label: "Adquirente é entidade de saúde",
    options: [
      { value: "HEALTH_ENTITY", label: "Entidade de saúde" },
      { value: "NOT_HEALTH_ENTITY", label: "Não é entidade de saúde" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.ibs_cbs_immunity_status",
    label: "Imunidade ao IBS/CBS",
    options: [
      { value: "IMMUNE", label: "Imune" },
      { value: "NOT_IMMUNE", label: "Não imune" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.effective_buyer_status",
    label: "Entidade qualificada é a adquirente efetiva",
    options: [
      { value: "CONFIRMED", label: "Confirmado" },
      { value: "NOT_CONFIRMED", label: "Não confirmado" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.cebas_status",
    label: "Situação do CEBAS",
    options: [
      { value: "VALID", label: "Válido" },
      { value: "INVALID", label: "Inválido" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.sus_service_requirement_status",
    label: "Requisito legal de prestação ao SUS",
    options: [
      { value: "SATISFIED", label: "Satisfeito" },
      { value: "NOT_SATISFIED", label: "Não satisfeito" },
      UNKNOWN_OPTION,
    ],
  },
];

type Result = {
  status: string;
  ruleset: { ruleset_id: string; version: string; content_hash: string };
  missing_facts: string[];
  official_candidates: {
    cst: string;
    cst_description: string;
    cclasstrib: string | null;
    cclasstrib_name: string | null;
  }[];
  legal_references: {
    source_id: string;
    act_type: string;
    number: string;
    year: number;
    issuing_authority: string;
    device: string;
    official_uri: string | null;
  }[];
  decision_trace: {
    sequence: number;
    phase: string;
    description: string;
    outcome: string;
  }[];
};

export function AssistedConsultationMedicamentos() {
  const [scenario, setScenario] = useState<Scenario>("RT-IBSCBS-0004");
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void apiFetch("/taxonomy/ibs-cbs/catalogs?status=PUBLISHED").then(async (response) => {
      if (response.ok) setCatalogs((await response.json()) as Catalog[]);
    });
  }, []);

  const fields = scenario === "RT-IBSCBS-0004" ? FIELDS_0004 : FIELDS_0005;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const now = new Date().toISOString();
    const productAttributes: Record<string, string> = {};
    if (scenario === "RT-IBSCBS-0004") {
      productAttributes["product.ncm_sh"] = String(data.get("product.ncm_sh") ?? "");
    }
    for (const field of fields) {
      productAttributes[field.name] = String(data.get(field.name) ?? "UNKNOWN");
    }
    const response = await apiFetch("/tax/ibs-cbs/classify", {
      method: "POST",
      body: JSON.stringify({
        evaluation_id: crypto.randomUUID(),
        ruleset_id: RULESETS[scenario].rulesetId,
        catalog_version_id: data.get("catalog_version_id"),
        operation_date: data.get("operation_date"),
        evaluated_at: now,
        known_at: now,
        product_attributes: productAttributes,
      }),
    });
    if (!response.ok) {
      const problem = (await response.json()) as { detail?: string };
      setError(typeof problem.detail === "string" ? problem.detail : "Consulta indisponível.");
      setResult(null);
      return;
    }
    setResult((await response.json()) as Result);
    setError("");
  }

  return <section>
    <div className="scope-warning">
      <strong>REGRAS PILOTO REAIS</strong> — escopo exclusivo de {scenario} ({RULESETS[scenario].title}).
      A análise é determinística, usa o ruleset explícito {RULESETS[scenario].rulesetId} e não presume
      fatos ausentes.
    </div>
    {scenario === "RT-IBSCBS-0004" && <div className="curation-warning" role="alert">
      <strong>Hipótese historicamente encerrada.</strong> O Anexo XIV foi revogado com efeitos em
      14/01/2026 e substituído, a partir dessa data, por uma lista dinâmica de medicamentos (art. 146,
      § 3º, atualizada a cada 120 dias por ato conjunto do Ministério da Fazenda e do Comitê Gestor do
      IBS). Esta regra só se aplica a operações entre 01/01/2026 e 13/01/2026 — para qualquer data
      posterior, o resultado será sempre &quot;sem classificação&quot; por esta regra. A hipótese
      correspondente à lista dinâmica (RT-IBSCBS-0002) ainda não foi implementada: até 2026-09-07,
      nenhum ato oficial publicado em cgibs.gov.br contém essa lista.
    </div>}
    <section className="object-kind-entry" aria-labelledby="medicamentos-scenario-title">
      <header><div><span className="eyebrow">Cenário</span>
        <h2 id="medicamentos-scenario-title">Qual hipótese de alíquota zero será analisada?</h2></div>
      </header>
      <div className="object-kind-grid">
        {(Object.keys(RULESETS) as Scenario[]).map((key) =>
          <button
            type="button"
            key={key}
            className={key === scenario ? "object-kind-active" : ""}
            aria-pressed={key === scenario}
            onClick={() => { setScenario(key); setResult(null); setError(""); }}
          >
            <strong>{key}</strong>
            <span>{RULESETS[key].title}</span>
          </button>
        )}
      </div>
    </section>
    <form className="consultation-form" onSubmit={submit} key={scenario}>
      <fieldset>
        <legend>1. Catálogo e vigência</legend>
        <div className="inline-form compact-form">
          <label>Data da operação
            <input
              name="operation_date"
              type="date"
              required
              min={scenario === "RT-IBSCBS-0004" ? "2026-01-01" : undefined}
              max={scenario === "RT-IBSCBS-0004" ? "2026-01-13" : undefined}
            />
            {scenario === "RT-IBSCBS-0004" && (
              <small>Janela histórica: 01/01/2026 a 13/01/2026 (fim exclusivo em 14/01/2026).</small>
            )}
          </label>
          <label>Catálogo oficial publicado<select name="catalog_version_id" required defaultValue="">
            <option value="">Selecione</option>
            {catalogs.map((catalog) => <option key={catalog.id} value={catalog.id}>{catalog.version}</option>)}
          </select></label>
          <label>Ruleset piloto<input value={RULESETS[scenario].rulesetId} readOnly /></label>
        </div>
        {scenario === "RT-IBSCBS-0004" && <div className="inline-form compact-form">
          <label>NCM/SH verificada (evidência oficial, não inferida)
            <input name="product.ncm_sh" placeholder="Ex.: código confirmado no Anexo XIV" required />
          </label>
        </div>}
      </fieldset>
      <fieldset>
        <legend>2. Fatos da operação</legend>
        <div className="inline-form compact-form">
          {fields.map((field) => <label key={field.name}>{field.label}
            <select name={field.name} required defaultValue="UNKNOWN">
              {field.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>)}
        </div>
      </fieldset>
      <button type="submit">Executar consulta {scenario}</button>
    </form>
    {error && <p role="alert" className="curation-warning">{error}</p>}
    {result && <article className={`classification-result result-${result.status.toLowerCase()}`}>
      <span className="eyebrow">3. Resultado determinístico</span><h2>{result.status}</h2>
      <p><strong>Ruleset:</strong> {result.ruleset.ruleset_id} · versão {result.ruleset.version}</p>
      <p><strong>Fingerprint:</strong> <code>{result.ruleset.content_hash}</code></p>
      {result.missing_facts.length > 0 && <div className="missing-facts"><h3>Fatos necessários ausentes</h3>
        <ul>{result.missing_facts.map((fact) => <li key={fact}>{fact}</li>)}</ul></div>}
      <h3>4. CST e cClassTrib</h3>{result.official_candidates.length === 0 ? <p>Nenhuma classificação aplicável.</p> :
        <div className="candidate-grid">{result.official_candidates.map((candidate) => <section className="candidate-card" key={`${candidate.cst}-${candidate.cclasstrib}`}>
          <strong>CST {candidate.cst}</strong><span>{candidate.cst_description}</span>
          {candidate.cclasstrib && <><strong>cClassTrib {candidate.cclasstrib}</strong><span>{candidate.cclasstrib_name}</span></>}
        </section>)}</div>}
      <section className="evidence-block"><h3>5. Fundamento legal</h3>
        {result.legal_references.length === 0 ? <p>Nenhum fundamento aplicado.</p> : <ul>{result.legal_references.map((source) =>
          <li key={source.source_id}>{source.act_type} {source.number}/{source.year}, {source.device} — {source.issuing_authority}
            {source.official_uri && <> · <a href={source.official_uri}>fonte oficial</a></>}</li>)}</ul>}
      </section>
      <details open><summary>6. DecisionTrace auditável</summary><ol>{result.decision_trace.map((step) =>
        <li key={step.sequence}><strong>{step.phase}</strong>: {step.description} — {step.outcome}</li>)}</ol></details>
    </article>}
  </section>;
}
