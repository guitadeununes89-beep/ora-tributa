# Template de especificação jurídica de regra tributária

> Fonte canônica: JSON. Copie `RULE_SPECIFICATION_TEMPLATE.json` para
> `rules/specifications/<rule_id>.json`. O template vazio deve retornar `NOT_READY`; isso é esperado.
> O validador verifica estrutura e referências, não o mérito da interpretação jurídica.

## Lifecycle documental

```text
DRAFT → IN_REVIEW → APPROVED → IMPLEMENTED → SUPERSEDED
```

- `DRAFT`: elaboração incompleta; não autoriza implementação.
- `IN_REVIEW`: submetida à revisão jurídica; não autoriza implementação.
- `APPROVED`: revisão e aprovação identificadas; único estado que pode retornar
  `READY_FOR_IMPLEMENTATION`.
- `IMPLEMENTED`: registra `tax_rule_identity_id`, `tax_rule_version_id` e data de implementação.
- `SUPERSEDED`: preserva o documento e aponta para a especificação substituta.

Transições são revisadas pelo Git nesta etapa. Não altere retroativamente uma versão aprovada:
crie nova `specification_version`.

## Campos obrigatórios

### Identidade e escopo

- `rule_id`, no padrão `RT-IBSCBS-0001`;
- `specification_version` inteira e positiva;
- `is_synthetic`;
- `title`;
- `tax_domain`, inicialmente `IBS_CBS`;
- `objective`;
- `jurisdiction`;
- `status`.

### Fundamento e proveniência

- `legal_foundation.legal_source_id`, referenciando fonte cadastrada da organização;
- `source_title` somente para identificação humana, sem substituir a fonte persistida;
- `specific_device`;
- `official_url`;
- `verifiable_reference`;
- `effective_from` inclusivo;
- `effective_to` exclusivo ou `null`, explicitamente informado.

O pre-flight confirma a existência da fonte, mas não decide se ela sustenta juridicamente a
interpretação.

### Catálogo normativo

- `catalog.catalog_version_id`, apontando para snapshot `PUBLISHED` da Etapa 5;
- `catalog.cst`;
- `catalog.cclasstrib`, quando aplicável, ou `null`.

Descrições oficiais não são copiadas para a especificação. O pre-flight consulta o snapshot exato e
confirma CST, cClassTrib e a relação estrutural entre ambos.

### Fatos, condições e resultado

- `required_facts` e `optional_facts`, com nome canônico, significado jurídico, tipo, valores
  permitidos e origem;
- `deterministic_conditions`, cada uma com identificador, descrição e fatos referenciados;
- `result`, com estado de classificação, CST, eventual cClassTrib e explicação;
- `exclusion_hypotheses`;
- `known_conflicts`;
- `precedence.precedes_rule_ids` e `precedence.legal_basis`.

Precedência não vazia sem fundamento explícito torna a especificação `NOT_READY`. NCM, descrição ou
qualquer fato isolado não recebe significado automático.

## Formato dos casos jurídicos

Cada grupo precisa ter pelo menos um caso:

- `positive_cases`;
- `negative_cases`;
- `insufficient_fact_cases`;
- `boundary_date_cases`.

Cada caso contém:

```json
{
  "case_id": "IDENTIFICADOR-UNICO",
  "description": "Motivo jurídico do cenário",
  "input": {"fact.path": "valor"},
  "expected": {
    "status": "NECESSITA_VALIDACAO",
    "cst": null,
    "cclasstrib": null,
    "missing_facts": ["fact.path"]
  }
}
```

O caso positivo deve representar aplicação; o negativo, situação próxima excluída; o inconclusivo,
fatos ausentes; e os limites devem cobrir início, fim e lados externos da vigência aplicável.

## Responsabilidade e aprovação

`approval` registra obrigatoriamente o elaborador. Para `APPROVED`, `IMPLEMENTED` e `SUPERSEDED`
também são obrigatórios revisor, aprovador, data e evidência verificável da aprovação.

O elaborador, revisor e aprovador devem ser pessoas/identidades rastreáveis. O pre-flight não
substitui segregação de funções nem assinatura jurídica.

## Mapeamento posterior

`implementation` permanece `null` até a regra ter sido tecnicamente implementada. No estado
`IMPLEMENTED`, deve conter:

- `tax_rule_identity_id`;
- `tax_rule_version_id`;
- `implemented_at`.

A futura `TaxRuleVersion` real deverá preservar ainda `rule_id`, `specification_version`,
`legal_source_id`, `catalog_version_id` e os metadados de aprovação. Não existe geração automática
de código a partir desta especificação.

## Validação

```bash
uv run validate-tax-rule-spec docs/tax/rules/specifications/RT-IBSCBS-0001.json \
  --organization-id <organization_id>
```

Saídas permitidas: `READY_FOR_IMPLEMENTATION` ou `NOT_READY`, sempre com a lista de problemas. O
exemplo em `examples/TEST-IBSCBS-0001.json` é inteiramente fictício, usa `example.invalid` e nunca
deve ser movido para a pasta de regras reais.