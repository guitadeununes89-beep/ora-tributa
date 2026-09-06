# Ora Tributa — pacote de continuidade para Claude

## Como começar

Leia, nesta ordem:

1. `AGENTS.md` — regras obrigatórias de segurança, arquitetura e governança tributária;
2. `README.md` — estado funcional, instalação e histórico das etapas;
3. `SPEC_PLATAFORMA_TRIBUTARIA.md` — escopo da plataforma;
4. `docs/adr/README.md` — índice das decisões arquiteturais;
5. `docs/tax/ETAPA_9_1_FINAL_APPROVAL_MATRIX.md` — estado jurídico atual do lote P1;
6. `docs/tax/ETAPA_9_2_ARCHITECTURE_REPORT.md` — arquitetura de transição e interação tributária.

As instruções de `AGENTS.md` prevalecem durante toda a continuidade. Não invente regra, alíquota,
classificação, exceção, vigência ou interpretação tributária.

## Estado atual consolidado — 2026-09-03

- Produto: **Ora Tributa**.
- Stack: Next.js/React/TypeScript, FastAPI/Python, PostgreSQL e `tax-engine` Python independente.
- Catálogo IBS/CBS governado: 164 cClassTrib na versão oficial de 23/06/2026.
- Cobertura executável: `1/164` (`0,61%`).
- Única regra real publicada: `RT-IBSCBS-0003`, somente no ruleset explícito
  `IBSCBS-PILOT-001`.
- `RT-IBSCBS-0007` v3: DRAFT, `READY_FOR_HUMAN_APPROVAL`.
- `RT-IBSCBS-0008` v3: DRAFT, `READY_FOR_HUMAN_APPROVAL`.
- `RT-IBSCBS-0009` v3: DRAFT, `BLOCKED_LEGAL_REFERENCE_CONFLICT`.
- Nenhuma das regras 0007–0009 possui `TaxRuleVersion` ou implementação.
- A divergência de 0009 é `art. 456` no catálogo versus `art. 460` na remissão do art. 463, I,
  da LC nº 214/2025. Não corrigir sem fonte oficial.

## Arquitetura tributária já decidida

- Regras publicadas e rulesets são imutáveis e temporalmente versionados.
- `tax-engine` não depende de FastAPI, SQLAlchemy, frontend, HTTP ou PostgreSQL.
- `DecisionTrace` explica por que um tratamento se aplica.
- `CalculationTrace` explica como um valor foi calculado.
- `TaxDomain` reconhece IBS, CBS, IS, ICMS e ISS e reserva extensibilidade para outros tributos.
- `TaxTransitionPeriod` e `TaxInteractionRule` estruturam a transição 2026–2033.
- Ausência de regra ou alíquota retorna incerteza explícita, nunca zero.
- Valores fiscais usam `Decimal`/`TaxDecimal`; `float` é proibido.
- Territórios incentivados usam o conceito governado futuro `TaxJurisdictionArea`; não codifique
  municípios, CEPs ou perímetros diretamente nas regras.

Consulte especialmente os ADRs 0002, 0003, 0006, 0007, 0010, 0015, 0017, 0021, 0022 e 0023.

## Limites jurídicos atuais

Não publicar 0007 ou 0008 apenas porque estão prontas para aprovação humana. Aprovação jurídica,
implementação, testes técnicos e publicação são gates separados. Não aprovar 0009 enquanto não
existir retificação ou confirmação oficial inequívoca.

A Etapa 9.2 criou apenas contratos e documentação para transição, IS, ICMS e ISS. Não existe cálculo
financeiro amplo produtivo, regra executável de IS, ruleset de ICMS/ISS ou rota real de simulação.

## Banco e dados

O banco em execução não faz parte do pacote. O estado estrutural é reproduzido pelas migrações e
seeds versionados. Artefatos normativos oficiais e seus manifestos estão em
`database/normative-artifacts/`.

Passos básicos:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
uv sync --all-packages --dev
uv run alembic upgrade head
$env:DEV_SEED_PASSWORD = "defina-uma-senha-local-segura"
uv run python database/seeds/development_governance.py
uv run python database/seeds/development_synthetic.py
```

`REAL_RULE_APPROVER_EMAIL` é necessário somente para recriar o aprovador governado no utilitário
histórico de implantação. Não versionar seu valor.

## Execução local

API:

```powershell
uv run uvicorn tributaria_api.main:app --app-dir backend/src --reload
```

Frontend:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Acessos: frontend `http://localhost:3000`, API `http://localhost:8000` e OpenAPI
`http://localhost:8000/docs` em desenvolvimento.

## Validação conhecida no momento do pacote

```powershell
uv run ruff check .
uv run mypy backend/src tax-engine/src importers/src
uv run pytest
cd frontend
pnpm lint
pnpm typecheck
pnpm test
```

Última execução: 119 testes Python passaram, 1 teste PostgreSQL opcional foi ignorado, 9 testes
frontend passaram, e Ruff, mypy, ESLint e TypeScript passaram.

## Próximo passo seguro

Obter aprovação humana formal e individual das versões DRAFT 0007 e 0008, sem publicação
automática. Paralelamente, monitorar apenas fontes oficiais para resolver 0009. Qualquer alteração de
fronteira, persistência, contrato público ou política de cálculo exige ADR antes da implementação.

## Conteúdo e exclusões do pacote

O pacote inclui código, testes, documentação, ADRs, migrações, seeds, artefatos normativos,
manifestações do catálogo, arquivos de CI e lockfiles. Não inclui `.git`, `.env`, banco em execução,
`.venv`, `node_modules`, `.next`, caches, logs, uploads ou builds.
