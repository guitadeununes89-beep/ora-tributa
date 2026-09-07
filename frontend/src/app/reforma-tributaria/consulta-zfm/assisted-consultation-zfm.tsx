"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Catalog = { id: string; version: string; status: string };
type Scenario = "RT-IBSCBS-0007" | "RT-IBSCBS-0008";

type FieldOption = { value: string; label: string };
type FieldSpec = { name: string; label: string; options: FieldOption[] };

const UNKNOWN_OPTION: FieldOption = { value: "UNKNOWN", label: "Não informado" };

const RULESETS: Record<Scenario, { rulesetId: string; cclasstrib: string; title: string }> = {
  "RT-IBSCBS-0007": {
    rulesetId: "IBSCBS-ZFM-0007-PILOT-001",
    cclasstrib: "200022",
    title: "Entrada de bem nacional na ZFM (art. 445)",
  },
  "RT-IBSCBS-0008": {
    rulesetId: "IBSCBS-ZFM-0008-PILOT-001",
    cclasstrib: "200023",
    title: "Bem intermediário entre indústrias na ZFM (art. 448)",
  },
};

const FIELDS_0007: FieldSpec[] = [
  {
    name: "operation.origin_area_status",
    label: "Origem da operação",
    options: [
      { value: "OUTSIDE_ZFM", label: "Fora da Zona Franca de Manaus" },
      { value: "INSIDE_ZFM", label: "Dentro da Zona Franca de Manaus" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.destination_area_status",
    label: "Destino da operação",
    options: [
      { value: "ZFM", label: "Zona Franca de Manaus" },
      { value: "OTHER", label: "Outro destino" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.material_good_status",
    label: "Natureza do objeto",
    options: [
      { value: "MATERIAL_GOOD", label: "Bem material" },
      { value: "NOT_MATERIAL_GOOD", label: "Não é bem material" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.industrialization_status",
    label: "Industrialização do bem",
    options: [
      { value: "INDUSTRIALIZED", label: "Industrializado" },
      { value: "NOT_INDUSTRIALIZED", label: "Não industrializado" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.origin_status",
    label: "Origem do bem",
    options: [
      { value: "NATIONAL", label: "Nacional" },
      { value: "FOREIGN", label: "Estrangeira" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.establishment_area_status",
    label: "Estabelecimento do adquirente",
    options: [
      { value: "ESTABLISHED_IN_ZFM", label: "Estabelecido na ZFM" },
      { value: "NOT_ESTABLISHED_IN_ZFM", label: "Não estabelecido na ZFM" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.taxpayer_status",
    label: "Adquirente é contribuinte do IBS/CBS",
    options: [
      { value: "TAXPAYER", label: "Contribuinte" },
      { value: "NOT_TAXPAYER", label: "Não contribuinte" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.art_442_habilitation_status",
    label: "Habilitação nos termos do art. 442",
    options: [
      { value: "VALID", label: "Válida" },
      { value: "INVALID", label: "Inválida" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.tax_regime_status",
    label: "Regime tributário do adquirente",
    options: [
      { value: "REGULAR_IBS_CBS", label: "Regime regular do IBS/CBS" },
      { value: "SIMPLES_NACIONAL", label: "Simples Nacional" },
      { value: "OTHER", label: "Outro regime" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.invoice_suframa_registration_status",
    label: "Inscrição Suframa no documento fiscal",
    options: [
      { value: "PRESENT_AND_MATCHING", label: "Presente e compatível" },
      { value: "ABSENT_OR_MISMATCH", label: "Ausente ou incompatível" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.art_443_par1_exclusion_status",
    label: "Exclusão do art. 443, § 1º",
    options: [
      { value: "NOT_EXCLUDED", label: "Não excluído" },
      { value: "EXCLUDED", label: "Excluído" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.zfm_entry_proof_status",
    label: "Comprovação de internamento",
    options: [
      { value: "CONFIRMED", label: "Confirmado" },
      { value: "NOT_CONFIRMED_AFTER_DEADLINE", label: "Não confirmado após o prazo" },
      { value: "PENDING_WITHIN_DEADLINE", label: "Pendente, dentro do prazo" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.entry_deadline_status",
    label: "Situação do prazo (120/210 dias)",
    options: [
      { value: "WITHIN_120_DAYS", label: "Dentro dos 120 dias" },
      { value: "VALID_EXTENSION_WITHIN_210_DAYS", label: "Prorrogação válida até 210 dias" },
      { value: "EXPIRED", label: "Prazo expirado" },
      UNKNOWN_OPTION,
    ],
  },
];

const FIELDS_0008: FieldSpec[] = [
  {
    name: "seller.establishment_zfm_relation",
    label: "Estabelecimento do fornecedor",
    options: [
      { value: "INSIDE", label: "Dentro da ZFM" },
      { value: "OUTSIDE", label: "Fora da ZFM" },
      { value: "BOUNDARY", label: "Sobre o limite territorial" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.establishment_zfm_relation",
    label: "Estabelecimento do adquirente",
    options: [
      { value: "INSIDE", label: "Dentro da ZFM" },
      { value: "OUTSIDE", label: "Fora da ZFM" },
      { value: "BOUNDARY", label: "Sobre o limite territorial" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "seller.zfm_incentivized_industry_status",
    label: "Fornecedor qualificado como indústria incentivada",
    options: [
      { value: "VALID", label: "Qualificação válida" },
      { value: "INVALID", label: "Qualificação inválida" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "buyer.zfm_incentivized_industry_status",
    label: "Adquirente qualificado como indústria incentivada",
    options: [
      { value: "VALID", label: "Qualificação válida" },
      { value: "INVALID", label: "Qualificação inválida" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.material_good_status",
    label: "Natureza do objeto",
    options: [
      { value: "MATERIAL_GOOD", label: "Bem material" },
      { value: "NOT_MATERIAL_GOOD", label: "Não é bem material" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.intermediate_good_status",
    label: "Bem intermediário para a operação",
    options: [
      { value: "INTERMEDIATE_GOOD", label: "Intermediário" },
      { value: "NOT_INTERMEDIATE_GOOD", label: "Não intermediário" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.delivery_area_status",
    label: "Local de entrega/disponibilização",
    options: [
      { value: "INSIDE_ZFM", label: "Dentro da ZFM" },
      { value: "OUTSIDE_ZFM", label: "Fora da ZFM" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.flow_type",
    label: "Natureza do fluxo",
    options: [
      { value: "DIRECT", label: "Operação direta" },
      { value: "TOLL_MANUFACTURING", label: "Industrialização por encomenda" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.taxable_scope_status",
    label: "Escopo tributável",
    options: [
      { value: "FULL_OPERATION", label: "Operação completa" },
      { value: "VALUE_ADDED_ONLY", label: "Somente valor adicionado" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "product.art_443_par1_exclusion_status",
    label: "Exclusão do art. 443, § 1º",
    options: [
      { value: "NOT_EXCLUDED", label: "Não excluído" },
      { value: "EXCLUDED", label: "Excluído" },
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

export function AssistedConsultationZfm() {
  const [scenario, setScenario] = useState<Scenario>("RT-IBSCBS-0007");
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void apiFetch("/taxonomy/ibs-cbs/catalogs?status=PUBLISHED").then(async (response) => {
      if (response.ok) setCatalogs((await response.json()) as Catalog[]);
    });
  }, []);

  const fields = scenario === "RT-IBSCBS-0007" ? FIELDS_0007 : FIELDS_0008;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const now = new Date().toISOString();
    const productAttributes: Record<string, string> = {
      "operation.zfm_area_version_id": String(data.get("operation.zfm_area_version_id") ?? ""),
    };
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
    <section className="object-kind-entry" aria-labelledby="zfm-scenario-title">
      <header><div><span className="eyebrow">Cenário</span>
        <h2 id="zfm-scenario-title">Qual operação da Zona Franca de Manaus será analisada?</h2></div>
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
        <legend>1. Catálogo e território</legend>
        <div className="inline-form compact-form">
          <label>Data da operação<input name="operation_date" type="date" required /></label>
          <label>Catálogo oficial publicado<select name="catalog_version_id" required defaultValue="">
            <option value="">Selecione</option>
            {catalogs.map((catalog) => <option key={catalog.id} value={catalog.id}>{catalog.version}</option>)}
          </select></label>
          <label>Versão territorial governada da ZFM
            <input name="operation.zfm_area_version_id" defaultValue="TJA-ZFM-V1" required /></label>
          <label>Ruleset piloto<input value={RULESETS[scenario].rulesetId} readOnly /></label>
        </div>
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
