# ADR-0025 — Avaliação multirregra e seleção de candidatos

- **Estado:** Aceito
- **Data:** 2026-09-08
- **Relacionados:** ADR-0008, ADR-0010, ADR-0011, ADR-0017

## Contexto

A Etapa 11 identificou que o ruleset combinado `IBSCBS-ZFM-PILOT-001` (RT-IBSCBS-0007 +
RT-IBSCBS-0008) sempre retorna `NECESSITA_VALIDACAO`. `TaxEngine.evaluate()`
(`tax-engine/src/tax_engine/engine.py`) agrega `missing_facts` como a união de **todas** as
regras do ruleset que retornaram `REQUIRES_VALIDATION`, sem distinguir "esta regra é só o
cenário errado, nunca foi de fato engajada" de "esta regra é candidata real e só falta um
fato". Esse é o comportamento deliberado do ADR-0008 — correto para uma única regra, mas errado
quando várias regras descrevem hipóteses mutuamente exclusivas. A correção aplicada até esta
etapa foi contornar o problema com "um ruleset por regra" (ADR-0017), o que funciona mas impede
qualquer consulta que precise perguntar "o que se aplica aqui" através de mais de uma regra.

`RuleDecisionStatus` (`MATCHED`/`NOT_MATCHED`/`REQUIRES_VALIDATION`) não distingue, dentro de
`REQUIRES_VALIDATION`, uma regra cujo próprio fato de escopo (o que sinaliza se a hipótese está
em jogo) ainda não foi informado, de uma regra cujo escopo já está confirmado mas falta outro
fato. Sem essa distinção, qualquer composição de regras herda o mesmo problema.

## Decisão

1. **Novo conceito de domínio, isolado do motor single-ruleset.** `tax-engine/src/tax_engine/
   multi_rule_evaluation.py` implementa `MultiRuleEngine`, que duplica deliberadamente o laço
   SELECTION → EVALUATION de `engine.py` em vez de modificá-lo — `TaxEngine.evaluate()` e as 5
   regras reais permanecem exatamente como estão, e o comportamento single-ruleset (ADR-0008)
   continua valendo sem alteração para todo o caminho já testado.
2. **`RuleCandidacyStatus`, computado por regra a partir da sua `RuleDecision` já existente,
   sem alterar `RuleDecisionStatus`:**
   - `MATCHED` → `SUPPORTED`.
   - `NOT_MATCHED` → `NOT_APPLICABLE`.
   - `REQUIRES_VALIDATION` com o fato de escopo da regra (`RuleScope.scope_facts`) já resolvido
     (fora do conjunto de `missing_facts`) → `SCOPE_CONFIRMED_INCOMPLETE`.
   - `REQUIRES_VALIDATION` com o próprio fato de escopo ainda ausente → `SCOPE_UNCONFIRMED`.
3. **`RuleScope` é metadado de composição, não conteúdo jurídico novo.** Cada entrada em
   `tax-engine/src/tax_engine/rule_scope_registry.py` nomeia o subconjunto dos `required_facts`
   já aprovados de uma regra que mais diretamente sinaliza se sua hipótese está em jogo — não
   introduz fato novo nem reinterpreta a regra. `scope_for()` recusa (`KeyError`) qualquer código
   de regra sem entrada explícita: nunca assume "tudo é escopo" nem "nada é escopo" por padrão,
   o que reintroduziria uma forma do próprio bug da Etapa 11.
4. **Agregação:** `missing_facts` da composição é a união apenas das regras
   `SCOPE_CONFIRMED_INCOMPLETE` (`SCOPE_UNCONFIRMED` nunca contribui — é isso que corrige o bug).
   Os candidatos são a união apenas das regras `SUPPORTED`. O `status` final reaproveita os
   4 valores já existentes de `ClassificationStatus`, **sem 5º valor**: `missing_facts` não vazio
   → `REQUIRES_VALIDATION`; mais de um candidato distinto → `POSSIBLE_MATCHES`; exatamente um →
   `CONCLUSIVE`; nenhum → `UNCLASSIFIED`.
5. **Decisão conservadora, deliberada e documentada aqui:** se uma regra já `SUPPORTED` produziu
   um candidato e outra regra com candidato de **chave idêntica** (mesmo caso de RT-IBSCBS-0003 e
   RT-IBSCBS-0005 no cClassTrib 200010) está `SCOPE_CONFIRMED_INCOMPLETE`, o resultado composto
   permanece `REQUIRES_VALIDATION` — não otimizamos "a chave já está coberta mesmo assim", porque
   isso exigiria expor `catalog_version_id`/`cst`/`cclasstrib` no protocolo `DeterministicRule`,
   o que este ADR não altera.
6. **Composições são sempre efêmeras.** `CandidateRuleSet` (o agrupamento em memória de N
   rulesets de regra única) nunca é persistido como `RuleSetRecord` — não existe "ruleset
   combinado" novo no banco, apenas a lista de `ruleset_ids` compostos, gravada em
   `evaluations.composed_ruleset_ids` (nova coluna, nula para avaliações single-ruleset).
7. **Migração de schema aditiva:** `evaluations.ruleset_id` passa a aceitar nulo (avaliações
   compostas não têm um único ruleset) e `composed_ruleset_ids` (JSONB, nulo por padrão) é
   adicionada. Nenhuma linha existente é afetada — todas já têm `ruleset_id` preenchido. Não foi
   necessária uma tabela de junção nova: `EvaluationRuleVersionRecord`
   (`evaluation_rule_versions`) já registrava, com posição, todas as versões de regra avaliadas
   (inclusive não casadas) desde a Etapa 1 — apenas não havia como uma avaliação apontar para
   várias rulesets ao mesmo tempo.
8. **Novo endpoint, puramente aditivo.** `POST /tax/ibs-cbs/classify-unified`
   (`UnifiedClassificationRequest`/`UnifiedClassificationResponse`) compõe N `ruleset_ids`; o
   endpoint existente `POST /tax/ibs-cbs/classify` (um único `ruleset_id`) não muda. O contrato do
   endpoint unificado duplica os campos de fato e o validador de allowlist do contrato existente
   (política já adotada nos CLIs de implantação: "duplicar, não extrair") em vez de generalizar o
   contrato de `/classify`, evitando qualquer risco às 3 telas piloto já em produção.
9. **Resolução de referência governada centralizada.** `governed_reference_resolution.py`
   substitui as 4 cópias locais de "resolver `legal_source_id`/`catalog_version_id` por URL
   oficial" espalhadas pelos CLIs de implantação (Etapas 10, 14, 15) por duas funções únicas, que
   agora também validam `content_hash` (obrigatório, bloqueante) e, opcionalmente, vigência
   (`as_of`) antes de vincular. O hash esperado é uma **constante pinada em cada CLI**, capturada
   uma vez do banco já confiável — nunca um campo novo nas especificações JSON já aprovadas, o
   que mudaria o documento canônico e invalidaria o hash de `approval_evidence` já registrado
   (`_approval_hash()` cobre o documento inteiro).

## Consequências

- a plataforma evolui de "uma tela por regra" para uma consulta unificada real, sem alterar
  nenhuma das 5 regras reais publicadas, seus rulesets, ou o ruleset combinado histórico
  (`IBSCBS-ZFM-PILOT-001`, que permanece intacto e imutável por trigger — ADR-0010);
- `RuleCandidacyStatus`/`RuleScope` passam a ser uma superfície de governança adicional: incluir
  uma regra futura na consulta unificada exige uma entrada revisada em `rule_scope_registry.py`,
  com a mesma seriedade de revisão de qualquer outro metadado governado;
- a resolução de referência centralizada bloqueia deploys cujo banco alvo tenha uma fonte legal
  com conteúdo divergente do esperado, tornando esse erro explícito em vez de silencioso;
- o caso "duas regras já `SUPPORTED` com chaves diferentes" continua retornando
  `POSSIBLE_MATCHES` sem desempate arbitrário, consistente com o restante da plataforma
  (AGENTS.md);
- as 3 telas piloto existentes (`/consulta-zfm`, `/consulta-medicamentos`) continuam
  funcionando sem nenhuma mudança; `/consulta` passa a servir o fluxo unificado.

## Alternativas consideradas

1. **Modificar `TaxEngine.evaluate()` para aceitar múltiplos rulesets diretamente:** rejeitada —
   arriscaria o comportamento single-ruleset já testado e usado pelas 3 telas piloto em produção.
2. **Adicionar um 5º valor a `ClassificationStatus` para "parcialmente aplicável":** rejeitada —
   os 4 valores existentes já expressam o resultado correto (`REQUIRES_VALIDATION`/
   `POSSIBLE_MATCHES`) sem introduzir um novo estado que toda a UI/API precisaria aprender.
3. **Persistir a composição como um novo `RuleSetRecord` combinado:** rejeitada — reintroduziria
   exatamente o problema da Etapa 11 (um ruleset publicado imutável bundlando regras mutuamente
   exclusivas) e tornaria a composição permanente em vez de uma escolha por consulta.
4. **Inferir automaticamente que uma chave já coberta por uma regra `SUPPORTED` dispensa outra
   regra `SCOPE_CONFIRMED_INCOMPLETE` de mesma chave:** rejeitada por exigir expor identificadores
   de classificação no protocolo `DeterministicRule` e por risco de mascarar um conflito real.
5. **Adicionar um campo de hash esperado às especificações JSON já aprovadas:** rejeitada —
   mudaria o documento canônico e invalidaria o hash de aprovação já registrado, exigindo nova
   aprovação fora do escopo desta etapa.
6. **Extrair um contrato/validador de fatos compartilhado entre `/classify` e
   `/classify-unified`:** rejeitada pela mesma política já aplicada aos CLIs de implantação —
   duplicar para preservar independência de evolução, não arriscar as telas já testadas.

## Critérios de revisão

Revisar antes de: adicionar uma 6ª regra real à consulta unificada (exige nova entrada em
`rule_scope_registry.py`); promover a consulta unificada a fluxo padrão de produção; introduzir
qualquer precedência tributária automática entre candidatos de chaves diferentes; ou expor
`catalog_version_id`/`cst`/`cclasstrib` no protocolo `DeterministicRule`.
