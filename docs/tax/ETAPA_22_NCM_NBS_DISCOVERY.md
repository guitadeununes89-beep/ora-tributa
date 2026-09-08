# Etapa 22 — Catálogos NCM/NBS e descoberta tributária assistida

- **Data:** 2026-09-08
- **Ator:** Guilherme Nunes, na capacidade de responsável tributário e jurídico do projeto
  (`legal-approver-guilherme-nunes`). Plano formal revisado e aprovado antes da implementação
  (Plan Mode), incluindo uma decisão explícita sobre a semente da camada de descoberta.
- **Decisão arquitetural:** [ADR-0026 — Catálogos NCM/NBS e descoberta tributária assistida](../adr/0026-catalogos-ncm-nbs-e-descoberta-tributaria.md).

## 1. Confirmação do fechamento da Etapa 21

Antes de iniciar, confirmei — não reimplementei — que a Etapa 21 está de fato fechada:

- Leitura de `docs/tax/ETAPA_21_UNIFIED_RULE_EVALUATION.md`, `docs/adr/0025-avaliacao-
  multirregra-e-selecao-de-candidatos.md` e dos testes (`tax-engine/tests/
  test_multi_rule_evaluation.py`, `backend/tests/test_evaluate_many.py`, `backend/tests/
  test_unified_classification.py`): documentação e testes coerentes entre si.
- `uv run pytest tax-engine backend/tests` → 223 passaram, 11 pulados (todos os Postgres-
  gated, esperado sem banco). `uv run ruff check .` e `uv run mypy backend/src tax-engine/src
  importers/src` sem problemas.
- Consulta unificada testada ao vivo no navegador nesta sessão (banco de demonstração real,
  login `analyst@example.invalid`): página carrega, os 5 rulesets continuam reproduzíveis.
- **Nenhuma pendência real encontrada.** A seção "Riscos remanescentes" do relatório da Etapa
  21 lista apenas decisões conservadoras já documentadas, nenhum bug ou trabalho inacabado.

## 2. Fontes oficiais (pesquisadas, baixadas e verificadas nesta sessão)

| Catálogo | Fonte | Formato | Vigência |
|---|---|---|---|
| NCM | `https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json` (Receita Federal/Siscomex) | JSON, ~3,1 MB, 15.156 entradas hierárquicas | Por código (`Data_Inicio`/`Data_Fim`); snapshot vigente em 08/09/2026, Resolução Gecex nº 926/2026 |
| NBS | `https://www.gov.br/mdic/pt-br/images/REPOSITORIO/scs/decos/NBS/NBSa_2-0.csv` (MDIC/RFB) | CSV Latin-1, 1.237 códigos | Tabela inteira: NBS 2.0, vigente desde 01/01/2019 (Portaria Conjunta RFB/SCS nº 1.429/2018 e nº 2.000/2018) |

Nenhuma das duas fontes publica hash oficial — `artifact_hash`/`normalized_hash` são calculados
nesta implantação, exatamente como já ocorre para o catálogo cClassTrib.

**Anexo VIII** (correlação oficial NBS↔cIndOp↔cClassTrib, RFB/Portal NFS-e,
`anexoviii-correlacaoitemnbsindopcclasstrib_ibscbs_v1-00-00.xlsx`) foi baixado e inspecionado:
1.739 linhas reais, mas os 27 cClassTrib distintos que cita (`000001`, `200016`, `200039` etc.)
**não incluem nenhuma** das 4 cClassTrib das 5 regras já publicadas (200009/200010/200022/
200023). É uma fonte real e válida para uma etapa futura de regras de serviços — documentada em
`tax_candidate_discovery.py` e nesta ADR, não usada agora.

## 3. O que foi carregado

Ambos os catálogos foram implantados via `governed_ncm_nbs_load_cli.py` (mesmo padrão de
`governed_load_cli.py`: manifesto versionado, verificação de hash, cadeia de ciclo de vida
completa com atores distintos) tanto no banco de testes quanto no banco de demonstração real:

- **NCM**: versão `2026-09-08`, `PUBLISHED`, 15.156 códigos (10.515 finais de 8 dígitos).
- **NBS**: versão `2.0`, `PUBLISHED`, 1.237 códigos.

## 4. Descoberta tributária: o que tem fundamento governado e o que não tem

- **NCM Capítulo 30 ("Produtos farmacêuticos") → RT-IBSCBS-0004/RT-IBSCBS-0005**: única
  relação com fundamento governado que aponta para uma regra hoje publicada. Fundamento: o
  próprio agrupamento oficial da tabela NCM (fato estrutural do governo) combinado com o
  escopo já declarado nas especificações aprovadas dessas duas regras — não é inferência por
  semelhança de descrição nem por IA. Decisão sua, explícita, tomada em Plan Mode.
- **Qualquer NCM fora do capítulo 30**: sem cobertura (`NO_COVERAGE`), fail-closed por
  desenho — `tax_candidate_discovery.NCM_CHAPTER_DISCOVERY.get()` nunca assume um padrão.
- **NBS (qualquer código)**: sem cobertura nesta etapa. O Anexo VIII existe e é real, mas
  wireá-lo agora só produziria "candidato identificado, sem regra disponível" em todo caminho
  de NBS — fica documentado como fonte real para quando a plataforma publicar regras de
  serviços.

## 5. O que ficou utilizável

- `GET /catalog-discovery/search?q=...` — busca literal, não-ranqueada, cruzando NCM, NBS e
  produtos internos. Retorna o objeto catalogado, nunca um tratamento tributário.
- `GET /catalog-discovery/candidates?ncm=...|nbs=...` — sempre 200; `NO_COVERAGE` é resposta
  normal, nunca erro.
- `/reforma-tributaria/consulta` ganhou o passo **"0. Pesquisar objeto"**, antes da seleção de
  regras já existente (Etapa 21) — mesma tela, mesmo componente, nenhuma tela nova por regra.
  Uma sugestão de descoberta apenas pré-marca os checkboxes já existentes; o usuário confirma e
  o motor continua exigindo os mesmos fatos de sempre.

## 6. Testes executados

- **Importadores** (`importers/tests/test_ncm_catalog.py`, `test_nbs_catalog.py`, 11 testes):
  parsing, zeros à esquerda preservados (`"0101.21.00"` → `"01012100"`), `level`/`is_final`
  corretos, datas convertidas, hashes estáveis, capítulo 30 presente.
- **Descoberta** (`tax-engine/tests/test_tax_candidate_discovery.py`, 4 testes): capítulo 30 →
  RT-0004/0005 em qualquer nível de código; qualquer outro capítulo NCM e qualquer NBS →
  `None` (fail-closed).
- **Repositório/versionamento/isolamento por organização** (`backend/tests/
  test_ncm_repository.py`, `test_nbs_repository.py`, 4 testes, SQLite em memória — mesmo padrão
  já usado por `test_taxonomy_repository.py`): busca por código/descrição, org A não vê o
  catálogo de org B.
- **Ciclo de vida**: `test_taxonomy_lifecycle.py` (já existente, genérico via `Protocol`) cobre
  NCM/NBS sem nenhuma mudança — `TaxonomyService`/`CatalogLifecyclePolicy` são reaproveitados
  sem alteração.
- **API** (`backend/tests/test_catalog_discovery.py`, 7 testes): busca cruzada, tolerância a
  catálogo sem versão publicada, os 3 estados de descoberta.
- **Integração com a consulta unificada** (`backend/tests/
  test_catalog_discovery_unified_integration.py`, Postgres-gated): descoberta por NCM capítulo
  30 → `ruleset_ids` reais → `evaluate_many()` roda normalmente, persiste `composed_ruleset_ids`.
- **Implantação em banco limpo**: `test_governed_deploy_cli_fresh_database.py` (Etapa 21)
  estendido para também rodar `governed_ncm_nbs_load_cli.py` — confirma os 2 catálogos
  `PUBLISHED` num banco descartável criado do zero.
- **Frontend** (`unified-consultation.test.tsx`, +2 testes): busca renderiza resultados e
  pré-marca regras corretas; `NO_COVERAGE` mostra a mensagem certa.
- **Suíte completa**: `uv run pytest` (267 testes com `POSTGRES_TESTS=1`, incluindo os novos),
  `uv run ruff check .`, `uv run mypy backend/src tax-engine/src importers/src`, `pnpm test`
  (23 testes), `pnpm lint`, `pnpm typecheck`, `pnpm build` — todos passando.

## 7. Demonstração ao vivo

Banco de demonstração real, API e frontend locais, login `analyst@example.invalid`, em
`/reforma-tributaria/consulta`:

1. **Caso com candidato**: pesquisa "heparina" → localiza NCM 3001 e NCM 30019010 ("Heparina e
   seus sais") no catálogo real. "Ver famílias de regras candidatas" em 30019010 → "Candidato
   identificado para NCM 30019010", com o fundamento, a fonte
   (`https://portalunico.siscomex.gov.br/classif`) e as condições exibidas. "Usar esta
   sugestão" pré-marca RT-IBSCBS-0004 e RT-IBSCBS-0005 na seção de candidatos.
2. **Caso inconclusivo**: prosseguindo com RT-0004/0005 pré-marcadas, preenchendo apenas os
   fatos que confirmam o escopo de RT-0005 (`buyer.health_entity_status=HEALTH_ENTITY`) sem
   completar os demais → `NECESSITA_VALIDACAO`, com "RT-IBSCBS-0005: Hipótese em jogo, mas
   fatos insuficientes" e os 4 fatos faltantes listados; RT-IBSCBS-0004 corretamente excluído
   dos fatos faltantes (`SCOPE_UNCONFIRMED`, nunca contaminando o resultado).
3. **Caso sem cobertura**: pesquisa "construção" → localiza dezenas de resultados reais em NCM
   (pedras, tijolos, máquinas) e NBS (serviços de construção). "Ver famílias de regras
   candidatas" em NBS 1.01 → "Descoberta ainda sem cobertura suficiente para NBS 1.01." —
   explícito, nunca silencioso, nunca uma regra genérica.

As três avaliações/buscas foram confirmadas persistidas corretamente no banco de demonstração
(`ruleset_id` nulo, `composed_ruleset_ids` preenchido) por consulta direta ao banco.

## O que isso NÃO faz

- Não publica nenhuma regra tributária nova nem aprova interpretação jurídica nova.
- Não atribui CST/cClassTrib apenas pelo NCM/NBS — a descoberta só sugere famílias de regras;
  cada regra continua exigindo seus próprios fatos para concluir.
- Não infere relacionamento por semelhança de descrição ou modelo de linguagem — a única
  relação com regra publicada (capítulo 30 → RT-0004/0005) usa um fato estrutural oficial da
  própria tabela NCM, combinado ao escopo já aprovado dessas regras.
- Não trata ausência de candidato como tributação geral — `NO_COVERAGE` é sempre explícito.
- Não implementa descoberta para NBS nesta etapa (Anexo VIII documentado, não usado).
- Não inicia cálculo financeiro amplo, XML/EFD, ou publicação de novas regras.
- Não altera nenhuma das 5 regras reais publicadas, seus rulesets, ou qualquer contrato/rota
  da Etapa 21 — `/catalog-discovery/*` é inteiramente aditivo.
