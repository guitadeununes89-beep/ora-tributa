# Etapa 23 — Consulta tributária em lote por Excel

- **Data:** 2026-09-09
- **Ator:** Guilherme Nunes, na capacidade de responsável tributário e jurídico do projeto
  (`legal-approver-guilherme-nunes`). Plano formal revisado e aprovado antes da implementação
  (Plan Mode).
- **Decisão arquitetural:** [ADR-0027 — Consulta tributária em lote por Excel](../adr/0027-consulta-tributaria-em-lote-por-excel.md).

## 1. Confirmação do fechamento da Etapa 22

Antes de iniciar, confirmei — não reimplementei — que a Etapa 22 estava de fato fechada:

- **5 regras reais `PUBLISHED`** (`RT-IBSCBS-0003/0004/0005/0007/0008`), confirmado por consulta
  direta ao banco (`tax_rule_versions`/`tax_rule_identities`), batendo com o README e o
  `CLAUDE_STATUS.md`.
- **4 cClassTrib distintos cobertos** (`200009`, `200010`, `200022`, `200023`), com overlap real
  entre `RT-IBSCBS-0003` e `RT-IBSCBS-0005` em `200010` (o caso de "chave compartilhada" já
  tratado pelo ADR-0025) — confirmado por consulta direta.
- **Consulta unificada funcional** (`/reforma-tributaria/consulta`,
  `POST /tax/ibs-cbs/classify-unified`) — confirmado no código e nos relatórios das Etapas 21/22.
- **Catálogos NCM (15.156 códigos) e NBS (1.237 códigos) `PUBLISHED`** — confirmado por consulta
  direta a `ncm_catalog_versions`/`nbs_catalog_versions`.
- **Descoberta fail-closed** (`tax_engine.tax_candidate_discovery`, `/catalog-discovery/*`) —
  confirmado no código e nos testes automatizados.
- **Testes e CI**: `uv run pytest` sem `POSTGRES_TESTS` → 256 passaram, 12 pulados (esperado);
  `ruff`/`mypy` limpos; CI do commit `6b19cae` (Etapa 22) verde.

**Achado real, registrado e corrigido nesta etapa (não é conteúdo tributário):** 3 regras
sintéticas de teste (`TEST-PG-RULE`, `TEST-QR-RULE-1`, `TEST-QR-RULE-2`) ficaram `PUBLISHED` por
engano no banco de demonstração, sobra de uma execução anterior de `POSTGRES_TESTS=1` apontada
para o banco errado. **Tentativa de limpeza autorizada e executada nesta sessão foi bloqueada
pelos próprios triggers de imutabilidade** (`published rulesets are immutable`,
`rule_lifecycle_events is append-only`) — exatamente o comportamento correto, já precedente da
Etapa 11. Nada foi apagado, nenhuma regra real foi tocada; as 3 linhas seguem permanentemente
imutáveis, isoladas (sem cClassTrib, sem `organization_id`, nunca aparecem em nenhuma consulta
real). O banco de teste local (`tributaria_test`) foi recriado do zero para eliminar a
contaminação cruzada de execuções anteriores.

## 2. O que foi implementado

Reaproveitando integralmente a consulta unificada (Etapa 21) e a descoberta (Etapa 22) — nenhum
motor novo, nenhuma regra tributária nova, nenhuma alteração em `Product`/`FactSet`/tax-engine:

1. **Importação de planilha** (`.xlsx` e `.csv`), com mapeamento de cabeçalho tolerante a
   acento/caixa e sem exigir todas as colunas presentes — colunas não reconhecidas viram fatos de
   contexto (`product_attributes`) em vez de serem descartadas.
2. **Processamento linha a linha**, cada linha independente: identificação do objeto (NCM, NBS,
   código interno com NCM cadastrado, ou descrição — nunca mais de um resultado de busca por
   descrição, sob risco de erro explícito em vez de escolha arbitrária) → descoberta → resolução
   de `ruleset_id` (via `GET /taxonomy/ibs-cbs/coverage`'s `list_rule_versions()`, sem
   hardcode) → `EvaluationService.evaluate_many()` real → mapeamento para os 4 status pedidos.
3. **Registro completo do lote**: identificador, organização, usuário, data, hash SHA-256 do
   arquivo (nunca o arquivo em si), quantidade de linhas, processadas, erros, versão do catálogo
   NCM/NBS/cClassTrib usada, versão do motor, `rule_codes`/`ruleset_ids` de descoberta por linha.
4. **API aditiva** `prefix=/batch-classification`: `POST /upload`, `POST /{id}/process`,
   `POST /{id}/reprocess` (nunca reescreve um lote concluído — cria um novo a partir das mesmas
   linhas cruas), `GET /{id}`, `GET /`, `GET /{id}/export`.
5. **Segurança de upload** (`AGENTS.md` §8): tamanho máximo configurável, apenas `.xlsx`/`.csv`,
   verificação de assinatura binária real, rejeição de `.xlsm`/`.xlsb`/`.xls` e de qualquer XLSX
   com macro embutida (`xl/vbaProject.bin`), proteção contra zip-bomb (limite de entradas e de
   tamanho descomprimido), `openpyxl` sempre em modo `data_only`/sem links externos.
6. **Interface** `/reforma-tributaria/consulta-lote`: upload → prévia (com avisos de cabeçalho
   não reconhecido e truncamento) → execução → grid de resultados com filtro por status →
   detalhe por linha (CST/cClassTrib, fundamento legal, fatos faltantes, observações,
   DecisionTrace auditável) → exportação `.xlsx` (colunas originais preservadas + colunas de
   conclusão/pendências/fundamento, células sanitizadas contra injeção de fórmula).

## 3. Limite inicial do lote

**500 linhas por processamento** (`BATCH_MAX_ROWS`, configurável por variável de ambiente) e
**5 MB por arquivo** (`BATCH_MAX_FILE_SIZE_BYTES`, idem) — **configuração inicial desta etapa, não
capacidade definitiva do produto**, conforme explicitamente pedido. Linhas além do limite são
reportadas como truncadas na resposta do upload, nunca processadas silenciosamente.

## 4. Testes executados

- **Importador** (`importers/tests/test_batch_workbook.py`, 14 testes): arquivo `.xlsx`/`.csv`
  válido, colunas ausentes toleradas, cabeçalho desconhecido reportado sem quebrar o arquivo,
  data inválida sinalizada sem lançar exceção, limite de linhas truncando com aviso, tipo de
  objeto normalizado, extensões com macro (`.xlsm`/`.xlsb`/`.xls`) rejeitadas, XLSX com
  `xl/vbaProject.bin` embutido rejeitado, extensão não suportada rejeitada, planilha vazia
  rejeitada.
- **Orquestração** (`backend/tests/test_batch_classification.py`, 16 testes, sem Postgres):
  identificação por NCM/NBS/código interno/descrição (incluindo formato inválido, código
  inexistente no catálogo publicado, descrição sem correspondência, descrição ambígua, roteamento
  por `object_kind`), NCM fora do capítulo 30 sem cobertura, candidato sem ruleset consultável
  vira `NECESSITA_VALIDACAO` fail-closed, resolução `rule_code`→`ruleset_id` via
  `list_rule_versions()` (ignora versões não publicadas, ignora regra sem ruleset consultável),
  `expand_row_result` lendo a avaliação real persistida (incluindo coerção de versão inteira para
  string).
- **Integração real** (`backend/tests/test_batch_classification_integration.py`, 6 testes,
  Postgres-gated, contra as 5 regras reais e os catálogos NCM/NBS já publicados): upload real →
  processamento real → item com candidato (capítulo 30, mesmo NCM 30019010 já demonstrado na
  Etapa 22) → `CONCLUSIVO` com `cclasstrib=200010` (RT-IBSCBS-0005 suportada, RT-IBSCBS-0004
  `SCOPE_UNCONFIRMED`) e `composed_ruleset_ids` reais persistidos; NCM fora do capítulo 30 →
  `SEM_COBERTURA_NORMATIVA`; NCM inexistente no catálogo → erro isolado, sem interromper a linha
  seguinte válida do mesmo lote; isolamento entre organizações (lote de uma organização
  invisível para outra); reprocessamento reproduz a mesma classificação com um `evaluation_id`
  novo (determinismo); exportação gera um `.xlsx` real, legível de volta, com colunas originais
  e de resultado.
- **Frontend** (`batch-consultation.test.tsx`, 5 testes): upload mostra prévia e avisos de
  cabeçalho; erro de upload exibido claramente; processamento mostra CST/cClassTrib/DecisionTrace
  de uma linha conclusiva; filtro por status funciona; link de exportação aponta para o endpoint
  correto e uma linha `ERROR` mostra sua mensagem.
- **Suíte completa**: `uv run pytest` → **286 passaram, 18 pulados sem `POSTGRES_TESTS=1`**
  (esperado); **304 passaram com `POSTGRES_TESTS=1`** contra um banco recriado do zero. `ruff
  check .` e `mypy backend/src tax-engine/src importers/src` limpos em 118 arquivos-fonte.
  `pnpm test` → **28 testes** (23 pré-existentes + 5 novos) em 9 arquivos; `pnpm lint`,
  `pnpm typecheck`, `pnpm build` limpos, incluindo a nova rota
  `/reforma-tributaria/consulta-lote`.

## 5. Exemplo de resultado (demonstração ao vivo)

Banco de demonstração real, migração 0010 aplicada, API e frontend locais, login
`analyst@example.invalid`, em `/reforma-tributaria/consulta-lote`. Planilha sintética de 3 linhas
(dados fictícios, não de cliente real):

| Linha | Código interno | NCM | Fatos informados | Resultado |
|---|---|---|---|---|
| 1 | SKU-CONCLUSIVO | 30019010 (capítulo 30) | Todos os fatos de escopo de RT-IBSCBS-0005 | **CONCLUSIVO** — CST 200 / cClassTrib 200010, via RT-IBSCBS-0005 v1, fundamento LC nº 214/2025 art. 146 § 1º II |
| 2 | SKU-INCONCLUSIVO | 30019010 (capítulo 30) | Só `buyer.health_entity_status` | **NECESSITA_VALIDACAO** — 6 fatos faltantes listados explicitamente (`product.kind`, `product.anvisa_registration_status`, `buyer.ibs_cbs_immunity_status` etc.) |
| 3 | SKU-SEM-COBERTURA | 01012100 (fora do capítulo 30) | — | **SEM_COBERTURA_NORMATIVA** — "Descoberta não encontrou nenhuma família de regra candidata governada para NCM 01012100" |

As três linhas foram confirmadas persistidas corretamente no banco de demonstração
(`classification_batches.status = COMPLETED`, `processed_count = 3`, `error_count = 0`;
`classification_batch_rows.discovery_rule_codes = ["RT-IBSCBS-0004","RT-IBSCBS-0005"]` nas linhas
1 e 2, `null` na linha 3) via consulta SQL direta. A exportação `.xlsx` foi confirmada real (200
OK, `content-type` de planilha, ~5,7 KB), com as colunas originais preservadas mais as colunas de
`status`/`cst`/`cclasstrib`/`tratamento`/`fundamento_legal`/`regra`/`fatos_faltantes`/
`observacoes` anexadas.

## 6. Cobertura executável antes/depois

**Inalterada: 4/164 cClassTrib (2,44%), antes e depois desta etapa.** O lote é uma forma de
acessar em volume a cobertura já existente das 5 regras publicadas — não cria, aprova nem publica
nenhuma regra ou interpretação jurídica nova.

## 7. Pendências

- Processamento é síncrono, dentro da própria requisição HTTP — RNF-08 (processamento em lote
  assíncrono, idempotente e reprocessável) permanece reconhecido como evolução futura, não
  implementado agora.
- `object_kind` do lote é só um rótulo de roteamento de busca (NCM vs. NBS quando não há código
  informado) — não implementa o `TaxObject` do ADR-0019; habilitar isso exige a evolução prevista
  nesse ADR, com migração e contrato próprios.
- A descoberta continua limitada ao Capítulo 30 da NCM → RT-IBSCBS-0004/0005 (Etapa 22); qualquer
  NCM fora dele ou qualquer NBS retorna `SEM_COBERTURA_NORMATIVA` no lote também, fielmente.
- Reprocessamento (`POST /{id}/reprocess`) existe e é testado no backend, mas não tem botão
  dedicado na interface desta etapa (não pedido explicitamente na especificação da Etapa 23).
- `RT-IBSCBS-0001/0002/0006/0009` seguem exatamente como estavam ao final da Etapa 20 — nenhuma
  ação desta etapa as afeta.

## 8. Próxima etapa recomendada

Duas frentes independentes, sem ordem obrigatória entre si:

1. **Processamento assíncrono real** (RNF-08): fila/worker para lotes maiores que o limite
   síncrono atual comporta, com acompanhamento de progresso granular na interface.
2. **Avançar a visão de e-Auditoria**: leitura de XML de NF-e/CT-e como uma nova fonte de
   identificação de objeto (além de NCM/NBS/código/descrição), reaproveitando a mesma
   descoberta e o mesmo motor desta etapa — não um pipeline de auditoria fiscal completo de uma
   vez.

## O que isso NÃO faz

- Não publica nenhuma regra tributária nova nem aprova interpretação jurídica nova.
- Não cria um segundo motor de avaliação — cada linha do lote usa exatamente
  `EvaluationService.evaluate_many()`, a mesma função da consulta unificada.
- Não atribui CST/cClassTrib apenas pelo NCM/NBS — a descoberta só sugere famílias de regras;
  cada regra continua exigindo seus próprios fatos para concluir.
- Não trata ausência de candidato ou de regra confirmada como tributação geral —
  `SEM_COBERTURA_NORMATIVA` é sempre explícito e distingue, no campo `observacoes`, "nenhum
  candidato de descoberta" de "candidato descartado pelos próprios fatos".
- Não armazena o arquivo original enviado — apenas o hash SHA-256, para auditoria.
- Não executa macro nem avalia fórmula de planilha; nunca resolve link/entidade externa do XLSX.
- Não implementa processamento assíncrono, XML/EFD, laudo com identidade visual de escritório ou
  simulador de regime — permanecem itens da visão de longo prazo (e-Auditoria), não desta etapa.
- Não altera nenhuma das 5 regras reais publicadas, seus rulesets, ou qualquer contrato/rota das
  Etapas 21/22 — `/batch-classification/*` é inteiramente aditivo.
