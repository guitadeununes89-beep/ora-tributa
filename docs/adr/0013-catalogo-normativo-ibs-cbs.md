# ADR-0013 — Catálogo normativo IBS/CBS

- **Estado:** Aceito
- **Data:** 2026-08-29

## Contexto

A plataforma passará a armazenar seu primeiro conteúdo tributário brasileiro real: a tabela
oficial de CST IBS/CBS e cClassTrib publicada pelo Portal Nacional da NF-e/ENCAT. O conteúdo não
pode ser transcrito manualmente, ativado no download, sobrescrito ou convertido silenciosamente
em regra de enquadramento de produtos.

O sistema já possui fonte legal, auditoria, autenticação, organizações, RBAC e lifecycle de regras.
Um catálogo tabular normativo, entretanto, possui artefato, schema, relatório de importação,
milhares de valores originais e comparação entre snapshots; forçá-lo no agregado de regra
tributária perderia essas invariantes.

## Decisão

### Escopo e fronteiras

- O catálogo é um agregado normativo próprio, independente do motor tributário e sem código de
  cálculo ou classificação produto/NCM.
- Catálogos e versões são escopados à organização autenticada. Uma organização não pode revisar,
  publicar nem consultar staging de outra. Esta decisão evita introduzir implicitamente um papel
  global da plataforma.
- Somente snapshots `PUBLISHED` são consultáveis como catálogo normativo ativo pelos usuários da
  organização. Histórico publicado permanece imutável.
- `LegalSourceRecord` será reutilizado para a fonte oficial; a versão do catálogo guarda a ligação
  exata com a fonte e o artefato.

### Pipeline e estados

O pipeline obrigatório é:

`artefato oficial → IMPORTED → VALIDATED → IN_REVIEW → APPROVED → PUBLISHED`.

Falha de hash, schema desconhecido crítico, versão ausente, campo obrigatório ausente ou código
duplicado coloca a importação em `FAILED`. `FAILED` não possui transição para publicação; exige
nova versão/importação. Download e importação nunca publicam automaticamente.

Permissões existentes serão reutilizadas:

- `CURATOR`: importar, validar e enviar para revisão;
- `APPROVER`: aprovar;
- `PUBLISHER`: publicar;
- qualquer papel com `READ`: consultar snapshots publicados e seus diffs.

A política de segregação de funções existente também vale para catálogo: importador/curador,
aprovador e publicador devem ser atores distintos quando SoD estiver habilitada.

### Artefato, staging e normalização

- O artefato original é preservado fora das tabelas de domínio, em caminho content-addressed e
  acompanhado de SHA-256. O banco armazena caminho relativo, mídia, tamanho e hash.
- Cada linha bruta é preservada em staging como JSON, com número da linha e erros estruturados.
- O parser suporta somente schemas explicitamente registrados por assinatura de cabeçalhos.
  Colunas extras não reconhecidas são preservadas, registradas como warning e impedem validação
  quando classificadas como críticas.
- Normalização é determinística: códigos permanecem strings com zeros à esquerda; textos têm
  espaços externos removidos e quebras normalizadas; células vazias viram `null`; indicadores
  são preservados como valores oficiais, sem inferência semântica.
- O hash normalizado é calculado sobre JSON canônico UTF-8 ordenado por cClassTrib e inclui todos
  os campos reconhecidos e valores originais preservados relevantes.

### Modelo e imutabilidade

Serão criadas as tabelas:

- `tax_classification_catalogs` — identidade estável do catálogo por organização;
- `tax_classification_catalog_versions` — publicação oficial, proveniência, hashes, status e
  relatório;
- `tax_classification_staging_rows` — linha original e diagnóstico;
- `ibs_cbs_csts` — CST observado na versão;
- `ibs_cbs_tax_classifications` — cClassTrib e vínculo ao CST na versão;
- `catalog_lifecycle_events` — transições append-only.

Versões publicadas e seus registros normalizados são imutáveis por trigger PostgreSQL. Nova
publicação oficial sempre cria outra versão. Uma única versão publicada pode ser marcada como
atual por catálogo/organização, sem apagar as anteriores.

### Diff e consulta

O diff é calculado de forma determinística pela chave cClassTrib e informa inclusões, remoções e
alterações campo a campo, incluindo CST, descrição, indicadores, observações e vigência. O
resultado inclui IDs, hashes e versões dos dois snapshots; ele não interpreta a relevância
jurídica da diferença.

Pesquisa textual é apenas recuperação literal/case-insensitive dos dados publicados. Ela não
ranqueia nem recomenda enquadramento.

## Consequências

- Há duplicação controlada de snapshots entre organizações que decidam curar a mesma fonte. É
  preferível à criação prematura de autoridade global; um catálogo compartilhado poderá ser
  proposto em ADR futuro.
- O parser precisa de revisão quando a assinatura de schema mudar, mesmo que a nova tabela pareça
  semelhante.
- Staging aumenta armazenamento, mas mantém evidência para auditoria e reprocessamento.
- O catálogo passa a conter dado normativo real, mas o motor tributário continua sem regra real
  executável e sem associação automática NCM/produto → cClassTrib.

## Alternativas consideradas

1. **Constantes Python:** rejeitada por impedir atualização, provenance e histórico confiáveis.
2. **Reusar `tax_rule_versions`:** rejeitada porque o agregado e as invariantes tabulares são
   materialmente diferentes.
3. **Catálogo global editável por qualquer `ADMIN`:** rejeitada por quebrar isolamento entre
   organizações e ampliar autoridade implicitamente.
4. **Publicar ao detectar nova versão na internet:** rejeitada; viola revisão humana e fail-closed.
5. **Inferir indicadores desconhecidos:** rejeitada; valores são preservados até documentação
   oficial suficiente.

## Critérios de revisão

Revisar este ADR antes de catálogo global, automação de descoberta/download, RLS, assinatura
digital de artefatos, múltiplos formatos oficiais ou uso do catálogo por regras executáveis.

