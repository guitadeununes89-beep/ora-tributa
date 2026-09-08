# Etapa 21 — Consulta unificada e composição segura de regras

- **Data:** 2026-09-08
- **Ator:** Guilherme Nunes, na capacidade de responsável tributário e jurídico do projeto
  (`legal-approver-guilherme-nunes`), a mesma capacidade já exercida em todas as aprovações
  anteriores. Plano formal revisado e aprovado antes da implementação (Plan Mode).
- **Decisão arquitetural:** [ADR-0025 — Avaliação multirregra e seleção de candidatos](../adr/0025-avaliacao-multirregra-e-selecao-de-candidatos.md).

## Diagnóstico

O ruleset combinado `IBSCBS-ZFM-PILOT-001` (RT-IBSCBS-0007 + RT-IBSCBS-0008), identificado na
Etapa 11, sempre retorna `NECESSITA_VALIDACAO`. A causa raiz está em
`tax-engine/src/tax_engine/engine.py`: `TaxEngine.evaluate()` agrega `missing_facts` como a
união de **todas** as `REQUIRES_VALIDATION` do ruleset antes de contar candidatos — correto para
uma única regra (ADR-0008), mas errado quando duas regras descrevem hipóteses mutuamente
exclusivas, porque a plataforma não tinha como distinguir:

- **regra não aplicável** (`NOT_MATCHED` — condição ativamente contradita);
- **regra potencialmente aplicável com fatos insuficientes, mas cujo próprio escopo já está
  confirmado** (ex.: já sabemos que a operação é de medicamento a entidade de saúde, só falta o
  CEBAS);
- **regra potencialmente aplicável cujo escopo em si ainda não foi informado** (ex.: nunca
  perguntamos se o fornecedor está dentro da ZFM);
- **conflito entre conclusões** (duas regras `SUPORTADAS` com candidatos de chave diferente, sem
  precedência jurídica aprovada).

A correção usada até esta etapa foi contornar o problema com "um ruleset por regra" (ADR-0017),
que funciona mas impede qualquer consulta que precise avaliar mais de uma hipótese ao mesmo
tempo — exatamente a limitação que esta etapa resolve.

## Solução implementada

Resumo executivo; a decisão completa, com alternativas consideradas, está no ADR-0025.

1. **`tax_engine.multi_rule_evaluation`** (novo módulo, tax-engine): `RuleCandidacyStatus`
   (`SUPPORTED` / `SCOPE_CONFIRMED_INCOMPLETE` / `SCOPE_UNCONFIRMED` / `NOT_APPLICABLE`),
   `RuleScope`, `CandidateRuleSet` (composição efêmera, nunca persistida como ruleset) e
   `MultiRuleEngine`, que reproduz a mesma SELECTION → EVALUATION de `engine.py` sem modificá-lo.
   A agregação só soma `missing_facts` de regras `SCOPE_CONFIRMED_INCOMPLETE` — regras
   `SCOPE_UNCONFIRMED` nunca contaminam o resultado. `ClassificationStatus` continua com os
   mesmos 4 valores, sem 5º estado novo.
2. **`tax_engine.rule_scope_registry`** (novo módulo): mapa fail-closed de `rule_code` →
   `RuleScope`, com uma entrada revisada para cada uma das 5 regras reais.
3. **Backend:** migração `0008_composed_evaluations` (`evaluations.ruleset_id` passa a aceitar
   nulo; nova coluna `composed_ruleset_ids`), 3 métodos novos em `SqlAlchemyGovernanceRepository`
   (`load_composable_rule`, `load_composed_rules`, `save_composed_evaluation`),
   `EvaluationService.evaluate_many()`, `multi_rule_evaluation_document()`, e o endpoint aditivo
   `POST /tax/ibs-cbs/classify-unified` (`UnifiedClassificationRequest`/
   `UnifiedClassificationResponse`). O endpoint de revisão de avaliação foi relaxado para aceitar
   `composed_ruleset_ids` como alternativa a `ruleset_id`.
4. **`governed_reference_resolution.py`** (novo módulo): centraliza `resolve_legal_source_id`
   (agora com validação **obrigatória** de `content_hash`, mais vigência opcional via `as_of`) e
   `resolve_catalog_version_id`, usados pelos 4 CLIs de implantação que antes duplicavam essa
   lógica localmente (`territory_governed_load_cli.py`, `real_rule_deploy_cli.py`,
   `real_rule_deploy_cli_p1_zfm.py`, `real_rule_deploy_cli_p2_medicamentos.py`). O hash esperado
   fica pinado como constante em cada CLI — nunca um campo novo nas especificações JSON já
   aprovadas (isso invalidaria o hash de `approval_evidence` já registrado).
5. **Frontend:** `/reforma-tributaria/consulta` passa a servir `unified-consultation.tsx`
   (objeto/operação → fatos iniciais → seleção de candidatos [checkboxes das 5 regras] → campos
   dinâmicos deduplicados → avaliação → conclusão ou pendências por regra). O componente
   RT-IBSCBS-0003-only anterior (`assisted-consultation.tsx`) foi removido por estar
   completamente substituído e sem outras referências. `/consulta-zfm` e
   `/consulta-medicamentos` permanecem inalterados, por compatibilidade durante a transição.

## Regras preservadas

Nenhuma das 5 regras reais publicadas, seus rulesets ou o conteúdo jurídico aprovado foi
alterado:

| Regra | Ruleset (inalterado) | cClassTrib |
|---|---|---|
| RT-IBSCBS-0003 | `IBSCBS-PILOT-001` | 200010 |
| RT-IBSCBS-0004 | `IBSCBS-PILOT-0004-001` | 200009 |
| RT-IBSCBS-0005 | `IBSCBS-PILOT-0005-001` | 200010 |
| RT-IBSCBS-0007 | `IBSCBS-ZFM-0007-PILOT-001` | 200022 |
| RT-IBSCBS-0008 | `IBSCBS-ZFM-0008-PILOT-001` | 200023 |

O ruleset combinado histórico `IBSCBS-ZFM-PILOT-001` (Etapa 11) permanece intacto, publicado e
imutável por trigger (ADR-0010) — não foi apagado nem modificado, apenas deixou de ser o único
caminho para avaliar as duas regras juntas.

## Testes executados

- **`tax-engine/tests/test_multi_rule_evaluation.py`** (11 testes, motor puro): RT-0007+RT-0008
  no mesmo contexto (ambas as direções); regra `NOT_APPLICABLE` não contamina; regra
  `SCOPE_CONFIRMED_INCOMPLETE` bloqueia a conclusão; RT-0003 vs RT-0005 (cClassTrib 200010
  compartilhado) — dedup para `CONCLUSIVE` e o caso conservador de `REQUIRES_VALIDATION`; janela
  de vigência da RT-0004 respeitada na seleção (dentro e fora da janela); duas regras sintéticas
  com chaves diferentes → `POSSIBLE_MATCHES` sem desempate arbitrário; reprodução determinística
  (mesmos fatos → mesmo `input_hash`/fingerprint/resultado); ausência de cobertura nunca vira
  candidato genérico (`UNCLASSIFIED`).
- **`backend/tests/test_evaluate_many.py`** (`EvaluationService`, requer Postgres com as 5 regras
  reais implantadas): reproduz o cenário exato da Etapa 11 (RT-0007+RT-0008, só os fatos da 0007)
  → `CONCLUSIVO`, RT-0008 `SCOPE_UNCONFIRMED`; confirma `ruleset_id IS NULL` e
  `composed_ruleset_ids` persistidos corretamente.
- **`backend/tests/test_unified_classification.py`** (7 testes, nível API/contrato): OpenAPI
  expõe o endpoint; catálogo não `PUBLISHED` é rejeitado; `ruleset_ids` duplicados/vazios são
  rejeitados; fatos não-governados continuam rejeitados; serialização de `rule_candidacies`.
- **`backend/tests/test_governed_deploy_cli_fresh_database.py`** (implantação real em banco
  limpo, Postgres): cria um banco descartável, roda `alembic upgrade head` e os 8 passos reais de
  implantação (seeds + 5 CLIs de carga/deploy) via subprocesso, confirma as 5 regras `PUBLISHED`,
  depois derruba o banco — prova que a carga não depende de UUID gerado em outra máquina.
- **`backend/tests/test_governed_reference_resolution.py`** (5 testes, Postgres): aceita
  hash/vigência corretos; recusa hash divergente; recusa fonte ainda não vigente na data pedida;
  recusa URL desconhecida; recusa cClassTrib fora da versão do catálogo pinada.
- **`frontend/.../unified-consultation.test.tsx`** (4 testes): nenhuma regra selecionada desabilita
  o envio; união de campos deduplicada entre RT-0007/RT-0008; aviso e campo de NCM só aparecem
  com RT-0004 selecionada; envio real compõe `ruleset_ids` corretamente e renderiza
  `rule_candidacies`.
- **Suíte completa:** `uv run pytest` (234 testes, com e sem `POSTGRES_TESTS=1`), `uv run ruff
  check .`, `uv run mypy backend/src tax-engine/src importers/src` (95 arquivos), `pnpm test` (21
  testes), `pnpm lint`, `pnpm typecheck`, `pnpm build` — todos passando.
- **Demonstração ao vivo no navegador** (banco de demonstração real, API e frontend locais,
  login `analyst@example.invalid`), em `/reforma-tributaria/consulta`:
  1. RT-IBSCBS-0007 isolada → `CONCLUSIVO` limpo (CST 200 / cClassTrib 200022) — a mesma prova já
     obtida em teste automatizado, mas agora através da interface real.
  2. RT-IBSCBS-0007 + RT-IBSCBS-0008 compostas, só os fatos da 0007 informados → `CONCLUSIVO`
     (não mais o `NECESSITA_VALIDACAO` do bug da Etapa 11), com RT-IBSCBS-0008 explicitamente
     listada como "hipótese ainda não confirmada" e os dois fatos de escopo pendentes nomeados.
  3. RT-IBSCBS-0003 + RT-IBSCBS-0005 compostas, só os fatos da 0003 informados → `CONCLUSIVO`
     com um único candidato (cClassTrib 200010, sem duplicação), RT-IBSCBS-0005 listada como
     pendente do fato `buyer.health_entity_status`.
  As três avaliações foram persistidas no banco de demonstração com `ruleset_id` nulo e
  `composed_ruleset_ids` corretamente preenchido, confirmado por consulta direta ao banco.

## Segurança e ambiente

- **Separação de banco de desenvolvimento e de testes:** os testes que dependem de PostgreSQL já
  eram isolados por `POSTGRES_TESTS=1`, mas **não são idempotentes contra um banco reutilizado**
  localmente — vários deles fazem `INSERT`/`session.commit()` direto com IDs fixos e nunca
  limpam. Isso é seguro em CI (banco `tributaria_test` efêmero, criado do zero a cada execução),
  mas rodar `POSTGRES_TESTS=1` repetidamente contra a mesma base local deixa linhas sintéticas
  permanentes (confirmado nesta etapa, ao recriar `tributaria_test` do zero várias vezes durante
  o desenvolvimento). **Risco documentado, não novo desta etapa:** recomenda-se nunca apontar
  `POSTGRES_TESTS=1` para o banco de demonstração (`tributaria`) — apenas para um banco
  descartável, exatamente como este trabalho fez.
- **CI atualizado** (`.github/workflows/ci.yml`) para também rodar os seeds e os 5 CLIs de
  implantação real contra o banco efêmero do job, com `REAL_RULE_APPROVER_EMAIL=ci-approver@example.invalid`
  — sem isso, `test_evaluate_many.py` e `test_unified_classification.py` (nível serviço) nunca
  exerceriam as regras reais em CI.
- **Auditoria de segredos/dados reais no repositório público** (agente dedicado, ver metodologia
  completa no histórico da sessão): nenhum segredo real, chave de API, senha não-placeholder,
  e-mail pessoal real ou CPF/CNPJ de pessoa física foi encontrado em nenhum arquivo rastreado.
  `.env` nunca foi commitado (confirmado via `git log --all --full-history -- .env`). Dois pontos
  para sua decisão, não corrigidos automaticamente nesta etapa:
  1. O nome completo "Guilherme Nunes" aparece como `display_name` literal em 4 scripts de CLI e
     em vários documentos de aprovação/ADR, como identidade do aprovador jurídico governado
     (`legal-approver-guilherme-nunes`). O e-mail correspondente nunca é hardcoded (sempre lido
     de `REAL_RULE_APPROVER_EMAIL`), mas o nome é um dado real indo para um repositório público —
     confirme se deve permanecer como está.
  2. A senha placeholder `tributaria` (usuário/senha do Postgres local) aparece idêntica em
     `docker-compose.yml`, `.github/workflows/ci.yml` e `.env.example`; aponta sempre para
     `localhost`/contêiner efêmero de CI, nunca um host real — prática padrão, mas sinalizado por
     completude.

## Riscos remanescentes

- A consulta unificada cobre apenas as 5 regras reais publicadas. Hipóteses ainda não
  implementadas (ex.: a lista dinâmica de medicamentos do art. 146, § 3º, RT-IBSCBS-0002) **não**
  são presumidas cobertas — a interface avisa isso explicitamente, mas depende do usuário ler o
  aviso antes de tirar conclusões sobre uma operação fora do escopo das 5 regras.
- A decisão conservadora do item 5 do ADR-0025 (não otimizar quando uma chave já está coberta por
  outra regra `SUPPORTED`) significa que compor RT-IBSCBS-0003 com RT-IBSCBS-0005 sempre que a
  0005 tiver algum fato de escopo respondido, mesmo incompleto, resulta em `REQUIRES_VALIDATION`
  em vez de `CONCLUSIVE` — comportamento correto e documentado, mas pode surpreender um usuário
  que espera "a 0003 já bastava".
- `rule_scope_registry.py` é fail-closed, mas isso significa que qualquer regra real futura fica
  automaticamente **inelegível** para a consulta unificada até alguém revisar e registrar seu
  `RuleScope` — não é um bug, é a salvaguarda deliberada, mas precisa ser lembrada no checklist de
  implantação de toda regra nova.
- O relaxamento do endpoint de revisão de avaliação (`review_classification`) para aceitar
  `composed_ruleset_ids` foi feito no nível da rota; `ProductTaxReviewRecord.ruleset_id`
  permanece nulo para avaliações compostas revisadas — nenhuma tabela nova foi criada para
  registrar individualmente quais rulesets compostos foram revisados (fora do escopo desta
  etapa, que expressamente não autoriza cálculo financeiro amplo).

## O que isso NÃO faz

- Não cria nenhuma regra tributária nova nem aprova interpretação jurídica nova.
- Não altera o conteúdo, a versão ou a aprovação de nenhuma das 5 regras reais publicadas.
- Não apaga nem modifica o ruleset combinado histórico `IBSCBS-ZFM-PILOT-001`.
- Não introduz precedência tributária entre candidatos de chaves diferentes.
- Não inicia cálculo financeiro amplo da Reforma Tributária.
- Não altera a visibilidade do repositório nem apaga histórico de commits.
