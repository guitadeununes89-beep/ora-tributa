# Especificação inicial — Plataforma de Inteligência Tributária

**Status:** produto local em evolução governada  
**Versão:** 0.8.0  
**Data:** 2026-09-01  
**Escopo desta versão:** Etapa 8 — experiência visual e mapa nacional dos 164 cClassTrib; somente RT-IBSCBS-0003 executável.


> **Leitura temporal:** as seções 1 a 24 registram decisões e estados históricos das respectivas
> etapas e não devem ser interpretadas isoladamente como estado corrente. O estado atual está
> consolidado na seção 25 (Etapa 23) e nos relatórios `docs/tax/ETAPA_21_UNIFIED_RULE_EVALUATION.md`,
> `docs/tax/ETAPA_22_NCM_NBS_DISCOVERY.md` e `docs/tax/ETAPA_23_BATCH_CONSULTATION.md`. Afirmações
> históricas como "nenhuma regra real executável" eram verdadeiras no fechamento daquela etapa e
> foram superadas pela publicação piloto da Etapa 7C e pelas etapas seguintes.
## 1. Visão

Construir uma plataforma profissional, modular, auditável e preparada para SaaS para inteligência, auditoria e planejamento tributário no Brasil. A primeira evolução funcional será orientada à Reforma Tributária — IBS, CBS e Imposto Seletivo — preservando espaço para ICMS, ICMS-ST, PIS/COFINS e outros domínios.

## 2. Objetivos da fundação

- separar interface, aplicação, domínio tributário, importação e persistência;
- tornar proveniência normativa e versionamento requisitos estruturais;
- impedir perda silenciosa de precisão monetária;
- definir estados explícitos de incerteza;
- permitir testes independentes e reprocessamento reproduzível;
- preparar CI, documentação e colaboração via Git/GitHub.

## 3. Fora do escopo atual

- regras ou alíquotas reais de IBS, CBS, Imposto Seletivo ou tributos legados;
- autenticação, cobrança, isolamento multi-tenant efetivo e permissões;
- importação produtiva de NF-e, CT-e, EFD ou Excel;
- classificação CST/cClassTrib;
- cálculos, créditos, split payment, simulação de preço e relatórios finais;
- uso de IA para conclusão fiscal.

## 4. Contextos e responsabilidades

### Interface (`frontend`)

Apresenta informações, coleta dados e exibe incerteza, fundamentos e memória de cálculo. Não contém regra tributária.

### Aplicação/API (`backend`)

Autentica futuramente, valida contratos, orquestra casos de uso, aplica autorização e chama o motor por interfaces explícitas.

### Motor tributário (`tax-engine`)

Biblioteca determinística, sem dependência de HTTP, UI ou ORM. Recebe fatos normalizados e um conjunto de regras versionado; produz resultado e trilha estruturada.

### Importadores (`importers`)

Preservam o arquivo original, extraem fatos, validam estrutura e reportam inconsistências. A decisão fiscal permanece no motor.

### Persistência (`database`)

Armazena dados operacionais, fontes, versões de regras, execuções e auditoria. A modelagem definitiva será precedida por ADR específico.

## 5. Requisitos funcionais da fundação

- RF-F01: disponibilizar uma página inicial mínima que identifique claramente o estado do produto.
- RF-F02: disponibilizar endpoint versionado de saúde da API.
- RF-F03: expor tipos de domínio para metadados de regra, referência legal, resultado de classificação e trilha de decisão.
- RF-F04: recusar `float` nos tipos monetários-base.
- RF-F05: representar os quatro estados de classificação obrigatórios.
- RF-F06: representar o ciclo de vida append-only e a aplicabilidade bitemporal de versões de regras.

## 6. Requisitos futuros já reconhecidos

Dashboard, empresas, produtos, consultas individual e em lote, IBS/CBS, CST, cClassTrib, Imposto Seletivo, auditorias de NF-e/CT-e, EFD ICMS/IPI e Contribuições, Excel, cadastro de produtos, comparação atual × reforma, planejamento 2027–2033, créditos, fornecedores, clientes, margem, preço, Split Payment, base legal, relatórios, memória de cálculo e trilha de auditoria.

Esses itens são visão de roadmap, não autorização de implementação.

## 7. Invariantes tributários

1. Toda regra possui identificador estável e versão imutável.
2. Toda versão registra fundamento, fonte, dispositivo, jurisdição, vigência e datas de sistema.
3. Uma conclusão aponta para as versões exatas das regras utilizadas.
4. Resultado inconclusivo lista dados ausentes ou causas da incerteza.
5. NCM/NBS são fatos entre outros; nunca são tratados automaticamente como decisão completa.
6. Cálculos usam aritmética decimal e política de arredondamento explícita.
7. Explicação por IA, quando existir, é marcada e vinculada ao resultado determinístico que explica.

## 8. Modelo conceitual mínimo

- `LegalSource`: ato normativo/fonte oficial e localização verificável.
- `TaxRuleIdentity`: identidade lógica estável da regra.
- `TaxRuleVersion`: conteúdo imutável e intervalo de vigência.
- `FactSet`: fatos normalizados da operação, produto, partes e período.
- `Evaluation`: execução reproduzível, com versões de código, regras e entrada.
- `DecisionTrace`: passos, condições, evidências e cálculos.
- `ClassificationOutcome`: estado, candidatos, dados ausentes e referências.

Os tipos atuais são sementes arquiteturais, não schema final de banco.

## 9. Estados de classificação

- `CONCLUSIVO`: há suporte determinístico suficiente para uma única conclusão.
- `POSSIVEIS_ENQUADRAMENTOS`: há mais de um candidato juridicamente possível e não existe critério seguro para desempate.
- `NECESSITA_VALIDACAO`: dados, interpretação ou evidência dependem de validação humana/especializada.
- `SEM_CLASSIFICACAO`: nenhuma regra aplicável ou base suficiente foi encontrada.

## 10. Auditabilidade mínima futura

Cada execução deverá registrar: identificador e horário; organização; hash/referência da entrada; versão do motor; conjunto e versões de regras; passos avaliados; valores intermediários em formato decimal; arredondamentos; resultado; alertas; ator/origem; correlação; e eventual explicação de IA separada.

## 11. Requisitos não funcionais

- RNF-01: tipagem estrita em Python e TypeScript.
- RNF-02: API versionada e contratos documentáveis por OpenAPI.
- RNF-03: módulos do motor testáveis sem banco ou rede.
- RNF-04: logs estruturados e correlação, sem dados fiscais sensíveis por padrão.
- RNF-05: evolução por migrações e compatibilidade controlada.
- RNF-06: segurança por padrão para uploads, XML e segredos.
- RNF-07: capacidade futura de isolamento por organização sem assumir banco separado nesta fase.
- RNF-08: processamento em lote futuro assíncrono, idempotente e reprocessável.

## 12. Critérios de aceite desta etapa

- estrutura do monorepo criada e documentada;
- frontend e backend mínimos inicializáveis após instalação das dependências;
- motor importável sem dependências da API;
- testes de invariantes-base presentes;
- ADRs iniciais registrados;
- CI e arquivos de colaboração GitHub presentes;
- nenhuma regra tributária real implementada.

## 13. Questões a decidir antes do primeiro módulo fiscal

- papéis, segregação de funções e assinatura no workflow de curadoria e aprovação jurídica;
- constraints do modelo físico bitemporal e granularidade de jurisdição;
- publicação atômica, assinatura e persistência do conjunto de regras;
- política normativa de precisão e arredondamento por tributo/operação;
- modelo de autorização, isolamento de tenant e retenção de documentos;
- arquitetura de filas e armazenamento de arquivos originais;
- formato de explicações e limites de uso de IA.
## 14. Segunda etapa — infraestrutura determinística

Implementado nesta versão:

- identidade lógica e snapshots imutáveis de regras;
- referência normativa separada e sintética nos testes;
- lifecycle append-only, com somente `PUBLISHED` elegível;
- separação entre `operation_date`, `known_at` e `evaluated_at`;
- rulesets ordenados, versionados e com fingerprint auditável;
- `FactSet`, quatro estados de classificação e `DecisionTrace` estruturada;
- envelope de `Evaluation` com hashes, versões e correlação;
- endpoint experimental `POST /api/v1/classifications/evaluate`;
- regras sintéticas explícitas para validar arquitetura e incerteza.

Critérios de aceite desta etapa:

- versões publicadas e históricas permanecem imutáveis;
- `DRAFT`, `IN_REVIEW`, `APPROVED`, `SUPERSEDED` e `WITHDRAWN` não são executados em avaliações novas;
- avaliações históricas podem usar a versão que estava publicada em `known_at`;
- limites inicial e final da vigência jurídica são testados;
- resultados conclusivo, múltiplo, incerto e sem classificação são testados;
- nenhuma regra brasileira real foi introduzida.

## 15. Terceira etapa — persistência e governança

Implementado nesta versão:

- modelo físico PostgreSQL para fontes, identidades, versões, lifecycle, rulesets, avaliações e auditoria;
- migrações Alembic versionadas como única via de alteração do schema;
- checks, chaves, locks e triggers para invariantes append-only e imutabilidade;
- workflow `DRAFT → IN_REVIEW → APPROVED → PUBLISHED`, com supersessão e retirada;
- segregação de funções configurável, ainda sem autenticação;
- publicação atômica e fingerprint estável de rulesets;
- ports de aplicação e adaptador SQLAlchemy fora do `tax-engine`;
- avaliação persistida, consulta da `DecisionTrace` e reprodução histórica;
- endpoints administrativos experimentais e tela `/curadoria`;
- seed de desenvolvimento restrito a `TEST-SOURCE-001`, `TEST-RULE-001` e `TEST-RULE-002`.

Critérios de aceite desta etapa:

- regras submetidas e rulesets publicados são imutáveis na aplicação e no PostgreSQL;
- somente versões publicadas entram em rulesets;
- falhas de publicação revertem a transação;
- ruleset publicado preserva lista e fingerprint;
- avaliações arquivam entrada mínima, hashes, versões e trilha sem documento fiscal completo;
- reprodução usa os mesmos fatos, `known_at`, motor e snapshot;
- todo conteúdo executável continua explicitamente sintético e allowlisted.
## Fundação de identidade e tenant — etapa 4

Implementado como infraestrutura inicial, sem regra fiscal real:

- identidade global, credencial local Argon2id e sessão revogável/expirável;
- organização ativa imutavelmente vinculada à sessão;
- membership com papéis explícitos `VIEWER`, `ANALYST`, `CURATOR`, `APPROVER`, `PUBLISHER` e
  `ADMIN`;
- autorização obrigatória no backend e ator derivado exclusivamente do contexto autenticado;
- empresas e estabelecimentos isolados por organização;
- avaliações vinculadas à organização e, opcionalmente, à empresa/estabelecimento, preservando
  esse contexto no histórico;
- auditoria de login bem-sucedido, alteração de membership, criação/estado de empresa e criação de
  estabelecimento;
- migração Alembic `0003_identity_tenancy` como única fonte de mudança do schema.

OIDC/SSO, MFA, convites e PostgreSQL RLS permanecem fora desta etapa e exigem ADR antes da adoção.


## Etapa 5 — Catálogo normativo CST IBS/CBS e cClassTrib

A plataforma admite snapshots oficiais versionados de CST IBS/CBS e cClassTrib com artefato,
staging, validação, revisão, aprovação, publicação, busca, histórico, diff e proveniência. Este
domínio permanece consultivo e separado do motor: não autoriza associação automática de NCM,
produto ou operação a uma classificação.
## 16. Etapa 6 — produtos e enquadramento assistido IBS/CBS

Implementado nesta versão:

- `Product` tenant-scoped, com código e unidade obrigatórios e GTIN, NCM e CEST opcionais;
- `ProductVersion` e atributos por versão imutáveis, com hash do snapshot e responsável;
- `ProductTaxReview` preparado para `CURRENT`, `REVIEW_RECOMMENDED` e `REVIEWED`;
- referências históricas da avaliação ao produto, versão do produto, ruleset e catálogo;
- `FactSet` ampliado com identidade/versão do produto, descrição e contexto operacional;
- candidatos estruturados CST/cClassTrib com suporte `SUPPORTED`, `PARTIALLY_SUPPORTED` ou
  `INSUFFICIENT_FACTS`, condições, fatos ausentes, regra e fontes;
- conflito sem precedência retornado como `POSSIVEIS_ENQUADRAMENTOS`;
- endpoint autenticado `POST /api/v1/tax/ibs-cbs/classify`;
- telas de produtos e consulta individual, com estados de incerteza visualmente distintos;
- auditoria cadastral e de solicitação/conclusão de classificação.

Invariantes específicas:

1. candidato executável aponta para a versão exata e `PUBLISHED` do catálogo da etapa 5;
2. o motor não acessa PostgreSQL nem duplica CST/cClassTrib;
3. fato manual conflitante com o snapshot do produto é rejeitado;
4. uma avaliação antiga preserva o `product_version_id`, o `catalog_version_id`, o ruleset, as regras,
   a entrada canônica e o trace;
5. nenhuma regra real é executável sem documento jurídico explicitamente `APPROVED`.

Não foram autorizados nem implementados XML, SPED, carga em massa ou cálculo financeiro IBS/CBS.
## 17. Etapa 7A — preparação das especificações jurídicas

A plataforma adota especificação JSON estrita, versionada no Git, antes da primeira implementação
real. O lifecycle documental é `DRAFT → IN_REVIEW → APPROVED → IMPLEMENTED → SUPERSEDED`; somente
`APPROVED` pode obter `READY_FOR_IMPLEMENTATION`.

O pre-flight valida schema, aprovação, temporalidade, fatos, condições, resultado, exclusões,
conflitos, precedência fundamentada, quatro grupos de casos e referências tenant-scoped à fonte e
ao snapshot `PUBLISHED` do catálogo CST/cClassTrib. Ele não avalia mérito jurídico e não gera código.

A futura `TaxRuleVersion` real deverá preservar `specification_id`, `specification_version`, fonte,
catálogo e metadados de aprovação. Antes disso, a etapa de implementação deverá adicionar o contrato
persistente de proveniência e testes associados. Os endpoints atuais permanecem fail-closed para
conteúdo real e aceitam somente fixtures explicitamente sintéticas.

As posições RT-IBSCBS-0001 a RT-IBSCBS-0005 foram apenas reservadas. Nenhuma contém tema, fonte,
CST, cClassTrib, vigência ou interpretação fiscal.
Esse era o estado no fechamento da Etapa 7A. O estado corrente das três primeiras posições está
documentado na Etapa 7B abaixo.

## 18. Etapa 7B — primeiras especificações jurídicas reais IBS/CBS

### Objetivo

Documentar as três primeiras hipóteses jurídicas reais de IBS/CBS em formato validável, usando
exclusivamente fontes oficiais e o catálogo oficial versionado da plataforma, sem criar regra
executável ou promover qualquer documento para `APPROVED`.

### Arquivos e regras documentadas

Foram criados:

- `docs/tax/rules/specifications/RT-IBSCBS-0001.json`: medicamento registrado na Anvisa com redução
  de 60%, ressalvadas as hipóteses de alíquota zero;
- `docs/tax/rules/specifications/RT-IBSCBS-0002.json`: medicamento registrado na Anvisa com alíquota
  zero por destinação sanitária prevista no art. 146;
- `docs/tax/rules/specifications/RT-IBSCBS-0003.json`: medicamento registrado na Anvisa adquirido
  por administração pública direta, autarquia ou fundação pública;
- `docs/tax/rules/ETAPA_7B_PESQUISA_JURIDICA.md`: fontes, temporalidade e pontos de revisão;
- `docs/tax/rules/PILOT_RULES_VALIDATION_REPORT.md`: consolidação do preflight e das pendências.

A matriz `docs/tax/rules/PILOT_RULES_MATRIX.md` registra as três regras como `DRAFT`.

### Lifecycle documental

As especificações seguem `DRAFT → IN_REVIEW → APPROVED → IMPLEMENTED → SUPERSEDED`. As três estão
em `DRAFT`; não possuem revisor, aprovador ou evidência de aprovação e não podem autorizar
implementação. A próxima etapa obrigatória é revisão jurídica humana.

### Conteúdo e limitações

Cada documento registra fundamento, dispositivo, fonte, vigência, fatos obrigatórios, condições,
exclusões, precedência quando expressa e casos positivos, negativos, inconclusivos e temporais.
CST/cClassTrib somente foram preenchidos após correspondência verificável no catálogo oficial.

Continuam pendentes o vínculo persistido da fonte e do snapshot `PUBLISHED`, decisões jurídicas
explicitamente sinalizadas, vocabulários canônicos e aprovação humana. O preflight real permanece
`NOT_READY` enquanto as referências governadas não puderem ser consultadas e, mesmo com referências
controladas como válidas, o status `DRAFT` resulta em `STATUS_NOT_APPROVED`.

### Ausência de execução

Nenhuma `TaxRuleVersion` real foi criada ou publicada. Nenhum ruleset tributário real foi publicado.
As três especificações não foram incorporadas ao `tax-engine`, não são retornadas como regra de
produção e não executam cálculo ou classificação tributária.

## 19. Etapa 7B.1 — saneamento das especificações piloto

### Objetivo

Incorporar a revisão jurídica intermediária sem promover, implementar ou publicar regra brasileira
real. O saneamento preserva incertezas como bloqueadores explícitos.

### Alterações documentais

- `RT-IBSCBS-0001` versão 2 distingue fornecedor, fabricante, importador e entidade responsável pelo
  art. 133, § 2º, e registra `NEEDS_LEGAL_VALIDATION_ART133_RESPONSIBLE_ENTITY`;
- `RT-IBSCBS-0002` versão 2 mantém a lista do § 3º como requisito conservador e registra
  `NEEDS_ART146_PAR3_OFFICIAL_LIST`;
- `RT-IBSCBS-0003` versão 2 preserva o inciso I separado do inciso II, mesmo com cClassTrib comum;
- `RT-IBSCBS-0004` documenta o caput original e o Anexo XIV até 13/01/2026;
- `RT-IBSCBS-0005` documenta separadamente o art. 146, § 1º, II;
- `RT-IBSCBS-0006` documenta o § 1º, III, bloqueado por regulamentação sanitária e lista oficial.

A matriz `docs/tax/rules/ART146_COVERAGE_MATRIX.md` cobre as duas redações temporais e identifica
as especificações ainda necessárias para os §§ 2º e 4º.

### Governança e validação

Todas as seis especificações permanecem `DRAFT`, sem mapeamento de implementação. A validação
estrutural controlada retorna apenas `STATUS_NOT_APPROVED`. O preflight governado permanece
`REFERENCE_LOOKUP_UNAVAILABLE` porque o PostgreSQL e os IDs persistidos não estão disponíveis.
Os marcadores não foram substituídos por IDs fabricados.

Nenhuma `TaxRuleVersion` real foi criada, nenhum ruleset brasileiro real foi publicado e nenhuma
das seis especificações está executável pelo `tax-engine`.

## 20. Etapa 7B.2 — referências governadas e pacote de revisão final

### Objetivo e gate intermediário

Resolver somente referências existentes no PostgreSQL e preparar as seis especificações para a
última revisão jurídica humana, sem promoção automática. O comando atual continua limitado a
`READY_FOR_IMPLEMENTATION` e `NOT_READY`; `READY_FOR_LEGAL_APPROVAL` é tratado apenas como avaliação
documental derivada, não como novo estado do lifecycle.

### Resultado da infraestrutura e das referências

O PostgreSQL 17.11 foi instalado localmente e o serviço `postgresql-x64-17` está ativo em
`localhost:5432`. `alembic upgrade head` aplicou com sucesso as migrações `0001` a
`0005_products_assisted`, confirmada como `head` por `alembic current`.

O inventário do banco confirmou zero organizações, fontes legais, catálogos, versões de catálogo,
CSTs, cClassTrib, versões de regra e rulesets. Consequentemente, nenhum `legal_source_id` ou
`catalog_version_id` foi resolvido e nenhum marcador foi alterado. O catálogo oficial local e seu
manifesto continuam íntegros, mas não existe snapshot persistido ou `PUBLISHED` no PostgreSQL.

### Matriz e priorização

`docs/tax/rules/LEGAL_APPROVAL_MATRIX.md` e
`docs/tax/rules/ETAPA_7B_2_FINAL_REVIEW_PACKAGE.md` consolidam referências, preflight, bloqueadores,
casos, precedência, cobertura temporal e as classes:

- A: `RT-IBSCBS-0003`;
- B: `RT-IBSCBS-0001`, `RT-IBSCBS-0004` e `RT-IBSCBS-0005`;
- C: `RT-IBSCBS-0002` e `RT-IBSCBS-0006`.

Classe A significa apenas candidata após resolver os vínculos governados e obter revisão humana.
Como o banco não contém as referências necessárias, nenhuma especificação está pronta para
submissão final nesta execução. As seis permanecem `DRAFT` e o preflight real retorna `NOT_READY`
por `STATUS_NOT_APPROVED`, `SOURCE_NOT_FOUND` e `CATALOG_VERSION_NOT_FOUND`.

### Limites

Nenhum conteúdo jurídico foi reinterpretado, nenhuma lacuna foi preenchida por inferência e nenhum
novo tratamento foi pesquisado. Não foi criada `TaxRuleVersion` real, não foi publicado ruleset
real e nenhuma das seis regras está executável pelo `tax-engine`.

## 21. Etapa 7B.3 — carga governada de fontes e catálogos oficiais

A implantação normativa não ocorre por migração ou `INSERT` manual. A rotina reproduzível
`tributaria_api.governed_load_cli` valida manifestos e hashes, preserva o artefato, importa para
staging, valida contagens e rejeições e percorre revisão, aprovação e publicação com segregação de
atores. Repetir o mesmo hash devolve a versão existente; reutilizar uma versão com artefato
divergente é conflito.

A organização fictícia `dev-governance-org` mantém `dev-curator`, `dev-approver` e `dev-publisher`.
Foram persistidas separadamente a LC 214/2025 original e compilada, a LC 227/2026 e a LC 187/2021.
O catálogo `IBSCBS-CCLASSTRIB` possui versões `2025-12-15` e `2026-06-23`, ambas `PUBLISHED`, com
proveniência, hash do artefato, fingerprint normalizado e lifecycle completo.

As seis especificações permanecem `DRAFT`, sem `implementation`. Suas fontes principais e versões
de catálogo agora usam IDs existentes no PostgreSQL. O preflight elimina falhas de referência e
preserva `STATUS_NOT_APPROVED`. A classe A (`RT-IBSCBS-0003`) indica apenas submissão possível à
revisão jurídica final; classes B e C mantêm bloqueadores normativos documentados.

Esta etapa não cria `TaxRuleVersion`, não publica ruleset tributário, não altera o comportamento do
`tax-engine` e não autoriza classificação ou cálculo real.
## 22. Etapa 7C — primeira regra tributária real e ruleset piloto

### Escopo e governança

Somente a `RT-IBSCBS-0003` versão 2 recebeu aprovação jurídica humana identificada e foi promovida
a `APPROVED`. A evidência registra pessoa, capacidade, data, ator governado e hash, sem persistir
CPF. O acúmulo de revisão e aprovação jurídica é exceção explícita deste piloto; curadoria técnica,
aprovação da versão e publicação permanecem rastreadas por atores distintos conforme ADR-0017.

### Persistência e proveniência

A migração `0006_first_real_tax_rule` permite identidades reais e adiciona à `TaxRuleVersion`
referências para specification ID/version/hash, fonte, catálogo, CST, cClassTrib e metadados de
aprovação. A identidade `RT-IBSCBS-0003` e sua versão 1 estão `PUBLISHED`, vigentes desde
01/01/2026, sem alteração destrutiva de histórico.

O ruleset `IBSCBS-PILOT-001` versão `1.0.0` está `PUBLISHED` e contém somente essa versão. Seu uso é
sempre explícito; não existe adoção silenciosa como ruleset default.

### Execução e auditabilidade

O registro allowlisted `REAL_RT_IBSCBS_0003_V1` resolve uma implementação Python independente de
FastAPI e PostgreSQL. A decisão requer os quatro fatos governados da especificação, respeita
vigência e produz `CONCLUSIVO`, `NECESSITA_VALIDACAO` ou `SEM_CLASSIFICACAO` sem inferência por NCM,
descrição, CNPJ ou nome. O `DecisionTrace` inclui condições, valores observados, regra/versão,
fonte, catálogo e códigos oficiais.

A API persiste entrada, hashes, versão do motor, ruleset/fingerprint, regra avaliada, resultado e
trilha. A reprodução compara entrada, ruleset e resultado arquivados. A interface identifica
visivelmente o escopo como **REGRA PILOTO REAL**.

### Limites

As especificações `RT-IBSCBS-0001`, `0002`, `0004`, `0005` e `0006` permanecem `DRAFT`, sem
`TaxRuleVersion` real e fora de rulesets reais. O piloto não verifica automaticamente a prova
material sanitária ou cadastral e não é uma configuração produtiva global. Detalhes e evidências
estão em `docs/tax/rules/RT-IBSCBS-0003_IMPLEMENTATION_REPORT.md`.
## 23. Etapa 8 — experiência visual e mapa nacional de cobertura IBS/CBS

### Estado atual do produto

O snapshot oficial `2026-06-23` contém 18 CST e 164 cClassTrib. A projeção nacional derivada do
ADR-0018 identifica 163 códigos com dispositivo oficial estruturado, 3 códigos cujo estado mais
alto é especificação `DRAFT` e 1 código com ao menos uma regra `PUBLISHED`. A cobertura executável
é `1/164`, ou `0,61%`. Esse percentual não afirma cobertura integral do cClassTrib 200010.

A `RT-IBSCBS-0003` continua sendo a única regra brasileira real executável e permanece no ruleset
piloto explícito. Nenhuma das outras cinco especificações foi promovida e nenhum dos demais códigos
do catálogo foi convertido em regra.

### Organização transversal

A expansão segue `catálogo oficial → fundamento legal → família jurídica → especificação → regra →
produto/serviço/operação`. A home e `/reforma-tributaria/cobertura` apresentam o catálogo nacional,
sem posicionar medicamentos como módulo central. Famílias jurídicas usam somente atributos e
dispositivos oficiais; setores comerciais não foram inferidos.

### API e interface

`GET /api/v1/taxonomy/ibs-cbs/coverage` produz métricas e os 164 itens. O detalhe
`GET /api/v1/taxonomy/ibs-cbs/coverage/{code}` inclui especificações, regras, bloqueadores e histórico
dos snapshots publicados. A projeção não possui tabela editável e não duplica lifecycle.

### Bens, serviços e identificadores

`FactSet` já admite NCM, NBS e atributos extensíveis. O ADR-0019 mantém o cadastro atual e planeja
objeto tributário e identificadores temporais para bens, serviços e direitos. Não houve migração nem
regra de serviços nesta etapa.

### Artefatos

- `docs/tax/IBSCBS_NATIONAL_COVERAGE_MATRIX.md` — inventário completo de 164 linhas;
- `docs/tax/IBSCBS_COVERAGE_ROADMAP.md` — prioridades por tipo oficial de alíquota;
- `docs/tax/IBSCBS_COMPLEMENTARY_TABLES_PLAN.md` — ingestão governada futura;
- `docs/tax/IBSCBS_SERVICES_AND_IDENTIFIERS.md` — NBS e objetos tributários;
- `docs/PRODUCT_VISUAL_REVIEW.md` e `docs/DEVELOPMENT_ACCESS.md`.


### 23.1 Fechamento visual da Etapa 8.1

O frontend passa a usar shell corporativo transversal com cabeçalho azul-marinho, menu lateral,
ações laranja, superfícies brancas e canvas cinza-claro. A alteração é exclusivamente de
apresentação e navegação: não cria regra, lifecycle, cálculo ou fonte normativa.

O inventário real contém 11 rotas, documentadas com título, finalidade, perfil e estado em
`docs/PRODUCT_VISUAL_REVIEW.md`. Módulos futuros aparecem desabilitados, sem rotas placeholder. A
home posiciona o universo de 164 cClassTrib acima do único piloto de medicamentos.

As evidências visuais reais permanecem pendentes porque a automação segura do navegador não iniciou
no sandbox Windows. Nenhum mockup substitui a evidência. A aplicação foi confirmada por respostas
HTTP, fluxo autenticado, API real, testes de componentes, lint, TypeScript e build.

## 24. Etapa 9 — famílias de cobertura e primeiro lote P1

### Projeção e interface

Conforme ADR-0020, `GET /api/v1/taxonomy/ibs-cbs/coverage` acrescenta `families`, uma projeção
aditiva derivada do indicador oficial `Tipo de Alíquota`. Cada família informa total, fundamentos
mapeados, códigos associados a DRAFT, aprovados, publicados, bloqueados e percentual executável.
Os estágios podem se sobrepor quando o mesmo código possui mais de uma especificação; isso preserva
a cardinalidade muitos-para-muitos e impede a premissa incorreta de uma regra por cClassTrib.

O menu mantém `/reforma-tributaria/cobertura`, visualmente subordinado à Reforma Tributária. Links
administrativos são filtrados por permissões do backend. O cabeçalho prepara os cinco contextos
futuros sem registrar dados reais. Módulos não implementados continuam sem rota. A consulta oferece
um seletor preparatório de tipo de objeto, mas somente `Produto/Mercadoria` está ativo; não houve
migração de `Product` nem ampliação do tax-engine.

### Lote P1

A comparação registrada em `docs/tax/ETAPA_9_P1_SELECTION.md` selecionou operações com bens na ZFM
e em ALC. O lote contém:

- `RT-IBSCBS-0007` — CST 200, cClassTrib 200022, arts. 442 e 445;
- `RT-IBSCBS-0008` — CST 200, cClassTrib 200023, art. 448;
- `RT-IBSCBS-0009` — CST 200, cClassTrib 200024, arts. 459, 460 e 463.

Todas estão `DRAFT`, com `implementation: null`, fatos obrigatórios, exclusões, casos positivos,
negativos, inconclusivos e temporais. O preflight real retorna apenas `STATUS_NOT_APPROVED`.
Regulamentação e prova de habilitação/ingresso, natureza intermediária, território, produção de
efeitos e a divergência art. 456/art. 460 permanecem bloqueadores explícitos.

### Cobertura e limites

A cobertura executável permanece `1/164` (`0,61%`). Aprovar os três documentos não criará execução;
somente após aprovação, implementação, testes e publicação futura o teto potencial seria `4/164`
(`2,44%`). Nenhuma nova TaxRuleVersion ou ruleset foi criada e o tax-engine não mudou.

## 25. Etapa 21, 22 e 23 — consulta unificada, catálogos NCM/NBS e consulta em lote (estado atual)

Esta seção consolida, de forma resumida, o estado real da plataforma após as três etapas mais
recentes — os relatórios completos ficam em `docs/tax/`, não duplicados aqui. **A cobertura
executável continua `4/164 cClassTrib` (2,44%)**: nenhuma das três etapas publicou regra
tributária nova; todas reaproveitam as 5 regras já publicadas (`RT-IBSCBS-0003/0004/0005/0007/
0008`).

- **Etapa 21 — consulta unificada e composição segura de regras** (ADR-0025,
  `docs/tax/ETAPA_21_UNIFIED_RULE_EVALUATION.md`): corrigiu a limitação de "uma regra por vez" —
  `POST /tax/ibs-cbs/classify-unified` avalia várias hipóteses candidatas na mesma passagem sem
  que uma hipótese não aplicável contamine o resultado de outra (`RuleCandidacyStatus`,
  `rule_scope_registry`). `/reforma-tributaria/consulta` passou a servir esse fluxo.
- **Etapa 22 — catálogos NCM/NBS e descoberta tributária assistida** (ADR-0026,
  `docs/tax/ETAPA_22_NCM_NBS_DISCOVERY.md`): catálogos oficiais governados de NCM (Siscomex/
  Receita Federal, 15.156 códigos) e NBS (MDIC/RFB, 1.237 códigos), com uma camada de descoberta
  fail-closed (`tax_engine.tax_candidate_discovery`) que hoje só relaciona o Capítulo 30 da NCM
  ("Produtos farmacêuticos") às regras RT-IBSCBS-0004/0005 já publicadas — qualquer outro NCM ou
  qualquer NBS retorna explicitamente "sem cobertura", nunca uma classificação presumida.
  `/catalog-discovery/search` e `/catalog-discovery/candidates` são inteiramente aditivos; o passo
  "0. Pesquisar objeto" da consulta unificada apenas pré-marca sugestões, nunca decide sozinho.
- **Etapa 23 — consulta tributária em lote por Excel** (ADR-0027,
  `docs/tax/ETAPA_23_BATCH_CONSULTATION.md`): primeira funcionalidade operacional de consulta em
  lote (`.xlsx`/`.csv`, limite inicial configurável de 500 linhas). Cada linha é processada de
  forma independente pela mesma consulta unificada e mesma descoberta das Etapas 21/22 — sem
  motor novo — distinguindo `CONCLUSIVO`, `POSSIVEIS_ENQUADRAMENTOS`, `NECESSITA_VALIDACAO` e
  `SEM_COBERTURA_NORMATIVA`. Uma linha inválida nunca interrompe o lote (vira `ERROR` isolado).
  `/reforma-tributaria/consulta-lote` cobre upload, prévia, execução, grid com filtro por status,
  detalhe com DecisionTrace e exportação — sem armazenar o arquivo original, sem processamento
  assíncrono nesta etapa (RNF-08 permanece reconhecimento futuro), sem implementar o `TaxObject`
  do ADR-0019 (o campo "tipo de objeto" do lote é só um rótulo de roteamento de busca).

Nenhuma das três etapas alterou `Product`, `FactSet` ou o `tax-engine` central; todas são
estritamente aditivas sobre a base da Etapa 20.
