"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";

type Catalog = { id: string; version: string; status: string };
type RuleCode =
  | "RT-IBSCBS-0003"
  | "RT-IBSCBS-0004"
  | "RT-IBSCBS-0005"
  | "RT-IBSCBS-0007"
  | "RT-IBSCBS-0008";

type FieldOption = { value: string; label: string };
type FieldSpec = { name: string; label: string; options: FieldOption[] };

const UNKNOWN_OPTION: FieldOption = { value: "UNKNOWN", label: "Não informado" };

// Duplicado deliberadamente a partir de consulta-zfm/consulta-medicamentos/consulta
// (RT-0003) - política já adotada nos CLIs de implantação: cada tela evolui de forma
// independente, sem uma abstração compartilhada arriscando as 3 telas piloto já
// testadas e em produção.
const RULESETS: Record<RuleCode, { rulesetId: string; cclasstrib: string; title: string }> = {
  "RT-IBSCBS-0003": {
    rulesetId: "IBSCBS-PILOT-001",
    cclasstrib: "200010",
    title: "Aquisição por autarquia/administração pública (art. 146, § 1º, I)",
  },
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

const FIELDS_0003: FieldSpec[] = [
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
    name: "buyer.legal_nature",
    label: "Natureza jurídica do adquirente",
    options: [
      { value: "DIRECT_PUBLIC_ADMINISTRATION_BODY", label: "Administração pública direta" },
      { value: "AUTARCHY", label: "Autarquia" },
      { value: "PUBLIC_FOUNDATION", label: "Fundação pública" },
      { value: "PUBLIC_COMPANY", label: "Empresa pública" },
      { value: "MIXED_CAPITAL_COMPANY", label: "Sociedade de economia mista" },
      { value: "PRIVATE_ENTITY", label: "Entidade privada" },
      UNKNOWN_OPTION,
    ],
  },
  {
    name: "operation.buyer_is_acquirer",
    label: "Adquirente efetivo?",
    options: [
      { value: "YES", label: "Sim" },
      { value: "NO", label: "Não" },
      UNKNOWN_OPTION,
    ],
  },
];

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

const FIELDS_BY_RULE: Record<RuleCode, FieldSpec[]> = {
  "RT-IBSCBS-0003": FIELDS_0003,
  "RT-IBSCBS-0004": FIELDS_0004,
  "RT-IBSCBS-0005": FIELDS_0005,
  "RT-IBSCBS-0007": FIELDS_0007,
  "RT-IBSCBS-0008": FIELDS_0008,
};

function mergedFields(selected: RuleCode[]): FieldSpec[] {
  const seen = new Map<string, FieldSpec>();
  for (const rule of selected) {
    for (const field of FIELDS_BY_RULE[rule]) {
      if (!seen.has(field.name)) seen.set(field.name, field);
    }
  }
  return [...seen.values()];
}

type RuleCandidacy = {
  rule_code: string;
  status: string;
  missing_facts: string[];
  unconfirmed_scope_facts: string[];
};

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
  evaluated_ruleset_ids: string[];
  rule_candidacies: RuleCandidacy[];
};

const CANDIDACY_LABELS: Record<string, string> = {
  SUPPORTED: "Suportada pelos fatos informados",
  SCOPE_CONFIRMED_INCOMPLETE: "Hipótese em jogo, mas fatos insuficientes",
  SCOPE_UNCONFIRMED: "Hipótese ainda não confirmada",
  NOT_APPLICABLE: "Não aplicável a este cenário",
};

export function UnifiedConsultation() {
  const [selected, setSelected] = useState<RuleCode[]>([]);
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void apiFetch("/taxonomy/ibs-cbs/catalogs?status=PUBLISHED").then(async (response) => {
      if (response.ok) setCatalogs((await response.json()) as Catalog[]);
    });
  }, []);

  const fields = useMemo(() => mergedFields(selected), [selected]);
  const needsAnnexXivWindow = selected.includes("RT-IBSCBS-0004");
  const needsZfmAreaVersion = selected.includes("RT-IBSCBS-0007");
  const needsNcmSh = selected.includes("RT-IBSCBS-0004");

  function toggleRule(rule: RuleCode) {
    setSelected((current) =>
      current.includes(rule) ? current.filter((item) => item !== rule) : [...current, rule],
    );
    setResult(null);
    setError("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selected.length === 0) {
      setError("Selecione ao menos uma hipótese para avaliar.");
      return;
    }
    const data = new FormData(event.currentTarget);
    const now = new Date().toISOString();
    const productAttributes: Record<string, string> = {};
    if (needsZfmAreaVersion) {
      productAttributes["operation.zfm_area_version_id"] = String(
        data.get("operation.zfm_area_version_id") ?? "",
      );
    }
    if (needsNcmSh) {
      productAttributes["product.ncm_sh"] = String(data.get("product.ncm_sh") ?? "");
    }
    for (const field of fields) {
      productAttributes[field.name] = String(data.get(field.name) ?? "UNKNOWN");
    }
    const response = await apiFetch("/tax/ibs-cbs/classify-unified", {
      method: "POST",
      body: JSON.stringify({
        evaluation_id: crypto.randomUUID(),
        ruleset_ids: selected.map((rule) => RULESETS[rule].rulesetId),
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
      <strong>CONSULTA UNIFICADA — REGRAS PILOTO REAIS</strong> — avalia, em uma única
      passagem, as hipóteses selecionadas abaixo. Cada regra mantém seu próprio ruleset
      publicado e sua própria memória de cálculo; a composição é apenas de orquestração,
      nunca de conteúdo jurídico novo. Hipóteses ainda não implementadas (por exemplo, a
      lista dinâmica de medicamentos do art. 146, § 3º — RT-IBSCBS-0002) não fazem parte
      desta consulta e não são presumidas cobertas.
    </div>
    <section className="object-kind-entry" aria-labelledby="unified-scenario-title">
      <header><div><span className="eyebrow">1. Candidatos</span>
        <h2 id="unified-scenario-title">Quais hipóteses tributárias podem se aplicar?</h2></div>
        <small>Marque uma ou mais — o motor decide com base apenas nos fatos informados.</small>
      </header>
      <div className="object-kind-grid">
        {(Object.keys(RULESETS) as RuleCode[]).map((rule) =>
          <button
            type="button"
            key={rule}
            className={selected.includes(rule) ? "object-kind-active" : ""}
            aria-pressed={selected.includes(rule)}
            onClick={() => toggleRule(rule)}
          >
            <strong>{rule}</strong>
            <span>{RULESETS[rule].title}</span>
            <small>{RULESETS[rule].rulesetId}</small>
          </button>,
        )}
      </div>
    </section>
    {needsAnnexXivWindow && <div className="curation-warning" role="alert">
      <strong>Hipótese historicamente encerrada.</strong> O Anexo XIV foi revogado com efeitos em
      14/01/2026 e substituído, a partir dessa data, por uma lista dinâmica de medicamentos (art. 146,
      § 3º). RT-IBSCBS-0004 só se aplica a operações entre 01/01/2026 e 13/01/2026.
    </div>}
    <form className="consultation-form" onSubmit={submit} key={selected.join("+")}>
      <fieldset>
        <legend>2. Fatos iniciais</legend>
        <div className="inline-form compact-form">
          <label>Data da operação
            <input
              name="operation_date"
              type="date"
              required
              min={needsAnnexXivWindow ? "2026-01-01" : undefined}
              max={needsAnnexXivWindow ? "2026-01-13" : undefined}
            />
          </label>
          <label>Catálogo oficial publicado<select name="catalog_version_id" required defaultValue="">
            <option value="">Selecione</option>
            {catalogs.map((catalog) => <option key={catalog.id} value={catalog.id}>{catalog.version}</option>)}
          </select></label>
          {needsZfmAreaVersion && <label>Versão territorial governada da ZFM
            <input name="operation.zfm_area_version_id" defaultValue="TJA-ZFM-V1" required /></label>}
          {needsNcmSh && <label>NCM/SH verificada (evidência oficial, não inferida)
            <input name="product.ncm_sh" placeholder="Ex.: código confirmado no Anexo XIV" required /></label>}
        </div>
      </fieldset>
      {selected.length > 0 && <fieldset>
        <legend>3. Perguntas adicionais (união das hipóteses marcadas)</legend>
        <div className="inline-form compact-form">
          {fields.map((field) => <label key={field.name}>{field.label}
            <select name={field.name} required defaultValue="UNKNOWN">
              {field.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>)}
        </div>
      </fieldset>}
      <button type="submit" disabled={selected.length === 0}>Executar consulta unificada</button>
    </form>
    {error && <p role="alert" className="curation-warning">{error}</p>}
    {result && <article className={`classification-result result-${result.status.toLowerCase()}`}>
      <span className="eyebrow">4. Avaliação</span><h2>{result.status}</h2>
      <p><strong>Regras compostas:</strong> {result.evaluated_ruleset_ids.join(", ")}</p>
      <p><strong>Fingerprint composto:</strong> <code>{result.ruleset.content_hash}</code></p>
      {result.missing_facts.length > 0 && <div className="missing-facts"><h3>Fatos necessários ausentes</h3>
        <ul>{result.missing_facts.map((fact) => <li key={fact}>{fact}</li>)}</ul></div>}
      <section className="evidence-block"><h3>5. Escopo avaliado por regra</h3>
        <ul>{result.rule_candidacies.map((candidacy) => <li key={candidacy.rule_code}>
          <strong>{candidacy.rule_code}</strong>: {CANDIDACY_LABELS[candidacy.status] ?? candidacy.status}
          {candidacy.status === "SCOPE_UNCONFIRMED" && candidacy.unconfirmed_scope_facts.length > 0 &&
            <> — para considerar esta hipótese, confirme: {candidacy.unconfirmed_scope_facts.join(", ")}</>}
        </li>)}</ul>
      </section>
      <h3>6. CST e cClassTrib</h3>{result.official_candidates.length === 0 ? <p>Nenhuma classificação aplicável.</p> :
        <div className="candidate-grid">{result.official_candidates.map((candidate) => <section className="candidate-card" key={`${candidate.cst}-${candidate.cclasstrib}`}>
          <strong>CST {candidate.cst}</strong><span>{candidate.cst_description}</span>
          {candidate.cclasstrib && <><strong>cClassTrib {candidate.cclasstrib}</strong><span>{candidate.cclasstrib_name}</span></>}
        </section>)}</div>}
      <section className="evidence-block"><h3>7. Fundamento legal</h3>
        {result.legal_references.length === 0 ? <p>Nenhum fundamento aplicado.</p> : <ul>{result.legal_references.map((source) =>
          <li key={source.source_id}>{source.act_type} {source.number}/{source.year}, {source.device} — {source.issuing_authority}
            {source.official_uri && <> · <a href={source.official_uri}>fonte oficial</a></>}</li>)}</ul>}
      </section>
      <details open><summary>8. DecisionTrace auditável</summary><ol>{result.decision_trace.map((step) =>
        <li key={step.sequence}><strong>{step.phase}</strong>: {step.description} — {step.outcome}</li>)}</ol></details>
    </article>}
  </section>;
}
