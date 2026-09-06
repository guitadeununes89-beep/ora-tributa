# API experimental de curadoria e classificação

> Exclusivamente para desenvolvimento com dados fictícios `TEST-*` e URLs `.invalid`. Os endpoints administrativos ainda não possuem autenticação e não podem ser expostos em produção.

## Endpoints administrativos

| Método | Caminho | Finalidade |
|---|---|---|
| `POST` | `/api/v1/admin/legal-sources` | Cadastrar fonte sintética. |
| `POST` | `/api/v1/admin/tax-rules` | Criar identidade lógica sintética. |
| `POST` | `/api/v1/admin/tax-rules/{id}/versions` | Criar snapshot `DRAFT`. |
| `POST` | `/api/v1/admin/tax-rule-versions/{id}/draft` | Editar conteúdo ainda `DRAFT` e recalcular hash. |
| `POST` | `/api/v1/admin/tax-rule-versions/{id}/submit-review` | `DRAFT → IN_REVIEW`. |
| `POST` | `/api/v1/admin/tax-rule-versions/{id}/approve` | `IN_REVIEW → APPROVED`. |
| `POST` | `/api/v1/admin/tax-rule-versions/{id}/publish` | `APPROVED → PUBLISHED`. |
| `POST` | `/api/v1/admin/tax-rule-versions/{id}/supersede` | `PUBLISHED → SUPERSEDED`. |
| `POST` | `/api/v1/admin/tax-rule-versions/{id}/withdraw` | `PUBLISHED → WITHDRAWN`. |
| `POST` | `/api/v1/admin/rulesets` | Criar snapshot com versões publicadas. |
| `POST` | `/api/v1/admin/rulesets/{id}/publish` | Publicar o ruleset atomicamente. |
| `GET` | `/api/v1/admin/tax-rules/{id}` | Consultar identidade e versões. |
| `GET` | `/api/v1/admin/tax-rule-versions` | Alimentar a tela técnica de curadoria. |
| `GET` | `/api/v1/admin/rulesets/{id}` | Consultar composição e fingerprint. |

`actor_id` é apenas um identificador declarado pelo cliente nesta etapa; não é autenticação. Todos os comandos exigem `correlation_id`, timestamps com timezone e dados explicitamente sintéticos.

## Fluxo mínimo

Após criar `TEST-SOURCE-001`, `TEST-RULE-001` e a versão `TEST-RULE-001-V1`, cada transição usa o mesmo formato:

```json
{
  "actor_id": "synthetic-reviewer",
  "correlation_id": "TEST-CORRELATION-REVIEW",
  "event_id": "TEST-EVENT-REVIEW-001",
  "occurred_at": "2040-01-02T12:00:00Z",
  "reason": "Synthetic workflow validation",
  "related_version": null
}
```

O `actor_id` deve mudar para aprovação e publicação quando `SEGREGATION_OF_DUTIES_ENABLED=true`.

Criação do ruleset:

```json
{
  "id": "TEST-RULESET-001",
  "name": "Synthetic governed snapshot",
  "version": "1",
  "created_at": "2040-01-05T12:00:00Z",
  "actor_id": "synthetic-curator",
  "correlation_id": "TEST-CORRELATION-RULESET",
  "rule_version_ids": ["TEST-RULE-001-V1"]
}
```

Publicação:

```json
{
  "occurred_at": "2040-01-06T12:00:00Z",
  "actor_id": "synthetic-ruleset-publisher",
  "correlation_id": "TEST-CORRELATION-RULESET-PUBLISH"
}
```

A publicação bloqueia o cabeçalho e a lista de membros. Se qualquer membro não estiver `PUBLISHED`, a transação inteira falha.

## Avaliação persistida

`POST /api/v1/classifications/evaluate`

```json
{
  "evaluation_id": "TEST-EVALUATION-001",
  "ruleset_id": "TEST-RULESET-001",
  "evaluated_at": "2040-06-15T12:00:00Z",
  "known_at": "2040-06-15T12:00:00Z",
  "correlation_id": "TEST-CORRELATION-EVALUATION",
  "facts": {
    "operation_date": "2040-06-15",
    "product_code": "SYNTHETIC-PRODUCT",
    "operation_type": "B",
    "product_attributes": {
      "synthetic_attribute_x": "A",
      "synthetic_attribute_z": "PRESENT"
    }
  }
}
```

Resposta resumida:

```json
{
  "evaluation_id": "TEST-EVALUATION-001",
  "engine_version": "0.3.0-experimental-persisted",
  "ruleset": {
    "ruleset_id": "TEST-RULESET-001",
    "version": "1",
    "content_hash": "<sha256 calculado do snapshot>"
  },
  "status": "CONCLUSIVO",
  "candidates": ["SYNTHETIC-Y"],
  "missing_facts": [],
  "decision_trace": ["<passos estruturados retornados pela API>"]
}
```

A avaliação arquiva `operation_date`, `known_at`, entrada canônica, `input_hash`, versão do motor, ruleset/fingerprint, versões usadas, resultado, `DecisionTrace` e correlação. Não armazena documento fiscal completo.

## Consulta e reprodução

- `GET /api/v1/classifications/evaluations/{evaluation_id}` retorna o envelope arquivado, as versões usadas e a trilha.
- `POST /api/v1/classifications/evaluations/{evaluation_id}/reproduce` recebe:

```json
{
  "evaluation_id": "TEST-EVALUATION-002",
  "evaluated_at": "2040-06-16T12:00:00Z",
  "actor_id": "synthetic-auditor",
  "correlation_id": "TEST-CORRELATION-REPRODUCTION"
}
```

A reprodução mantém fatos, `known_at` e snapshot originais. Novo horário, ID e correlação não alteram a decisão determinística.

## Limites de segurança

- `ADMIN_API_ENABLED=false` oculta o workflow administrativo;
- nenhum endpoint autentica `actor_id` nesta etapa;
- não enviar documentos fiscais, CNPJ real, PII, token, senha ou certificado;
- o backend resolve somente implementações sintéticas allowlisted;
- conteúdo persistido nunca é executado com `eval`, import dinâmico ou código vindo do banco;
- OpenAPI fica disponível em `/docs` somente fora de produção.
## Identidade e administração do tenant

- `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`
- `GET|POST /api/v1/companies`
- `PATCH /api/v1/companies/{id}/status`
- `GET|POST /api/v1/companies/{id}/establishments`
- `GET /api/v1/memberships`, `PATCH /api/v1/memberships/{id}`

Cookies são enviados com credenciais. Operações de escrita exigem também `X-CSRF-Token`. Os
comandos administrativos de regras não aceitam `actor_id`: o backend usa o usuário da sessão.


## Produtos e consulta assistida IBS/CBS

Estes endpoints exigem sessão, organização ativa, CSRF nas escritas e permissão adequada:

| Método | Caminho | Finalidade |
|---|---|---|
| `GET` | `/api/v1/products?q=` | Listar ou buscar produtos da organização. |
| `POST` | `/api/v1/products` | Criar produto e snapshot versão 1. |
| `GET` | `/api/v1/products/{product_id}` | Consultar versão atual e histórico. |
| `PATCH` | `/api/v1/products/{product_id}` | Criar nova versão imutável. |
| `POST` | `/api/v1/tax/ibs-cbs/classify` | Executar enquadramento assistido governado. |
| `POST` | `/api/v1/tax/ibs-cbs/evaluations/{evaluation_id}/review` | Registrar revisão humana vinculada aos snapshots. |

A consulta recebe `evaluation_id`, `ruleset_id`, `catalog_version_id`, `operation_date`, timestamps
com timezone e `product_id` ou fatos manuais explícitos. O catálogo e o ruleset devem ser snapshots
publicados. Quando um produto é usado, fatos manuais conflitantes são rejeitados.

A resposta mantém os quatro estados do domínio e inclui `tax_candidates`, `official_candidates`,
`missing_facts`, `rules_evaluated`, `legal_references`, versão/fingerprint do ruleset,
`catalog_version_id` e `decision_trace`. Cada candidato CST/cClassTrib é validado no mesmo snapshot
do catálogo antes da persistência. Candidatos legados sem proveniência de catálogo são recusados.

Como ainda não há regra jurídica real `APPROVED`, o endpoint não pode produzir uma conclusão fiscal
brasileira. Fixtures sintéticas existem somente em testes; não devem ser promovidas para produção.
## Pre-flight de especificações jurídicas

- `GET /api/v1/admin/tax-rule-specifications` lista readiness dos JSON canônicos conhecidos;
- `POST /api/v1/admin/tax-rule-specifications/{rule_id}/preflight` revalida um documento.

Ambos exigem sessão e papel de curadoria, usam a organização autenticada e nunca recebem tenant do
cliente. O resultado inclui `READY_FOR_IMPLEMENTATION` ou `NOT_READY`, campos resumidos e problemas
com código, caminho e mensagem. A resposta sempre declara que prontidão estrutural não comprova o
mérito da interpretação jurídica.