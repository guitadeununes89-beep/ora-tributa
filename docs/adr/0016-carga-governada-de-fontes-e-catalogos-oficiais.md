# ADR-0016 — Carga governada de fontes legais e catálogos oficiais

- **Estado:** Aceito
- **Data:** 2026-08-30
- **Responsáveis:** curadoria técnica, revisão, aprovação e publicação segregadas

## Contexto

A Etapa 5 criou o agregado de catálogo e seu pipeline, mas o banco local atual nasceu vazio: as
migrações não executam seeds normativos e nenhum processo administrativo de importação havia sido
executado neste cluster. O artefato oficial e seu manifesto estavam preservados no Git, porém isso
não equivale a persistência ou publicação no PostgreSQL.

O service genérico de `LegalSource` ainda bloqueava qualquer fonte não sintética. Além disso, o
contrato documental das especificações possuía somente uma fonte primária, embora algumas
especificações citem atos alteradores ou fundamentos complementares. A reexecução da carga também
dependia apenas de constraints do banco, sem resposta idempotente explícita.

`RT-IBSCBS-0004` usa o intervalo histórico de 01/01/2026 a 13/01/2026 e, portanto, não pode apontar
para o snapshot atual do catálogo. Seu vínculo exige o artefato histórico oficial correspondente.

## Decisão

1. Fontes oficiais reais serão aceitas pelo mesmo `GovernanceService`, exclusivamente para URLs
   HTTPS de autoridades oficiais permitidas, com hash SHA-256, organização, ator e auditoria. IDs
   reais serão UUIDs gerados pelo sistema; identificadores documentais `PENDING-*` nunca serão
   persistidos como chaves.
2. A criação de fonte será idempotente por organização e hash de conteúdo. Repetir a mesma carga
   retorna a fonte existente; mesmo identificador explícito com conteúdo divergente é conflito.
3. Especificações poderão registrar fontes adicionais estruturadas, com ID, dispositivo e papel da
   referência. O preflight validará cada ID no mesmo tenant. O status documental continuará
   independente dessas referências.
4. A organização local será a organização fictícia `dev-org`, criada pelo seed técnico existente.
   Curadoria, aprovação e publicação usarão usuários fictícios distintos e papéis compatíveis.
5. O XLSX sempre será processado pelo importador seguro da Etapa 5. A persistência seguirá
   `IMPORTED → VALIDATED → IN_REVIEW → APPROVED → PUBLISHED`, com atores distintos e eventos
   append-only.
6. A importação será idempotente por catálogo e `artifact_hash`. Mesmo `version` com artefato
   diferente será conflito explícito; artefato inválido ou hash divergente não poderá avançar.
7. O `artifact_hash` identifica os bytes originais. O `normalized_hash`, já persistido, é o
   fingerprint canônico do conteúdo normalizado do snapshot. Não será criado um hash redundante.
8. Snapshot atual e snapshot histórico são versões independentes e imutáveis do mesmo catálogo.
   Uma especificação só poderá receber o ID do snapshot temporalmente compatível.
9. A reprodução em novo ambiente será feita por comando idempotente, manifestos versionados,
   artefatos preservados e workflow governado; migração de schema não carregará dados normativos.
10. Nenhuma dessas operações cria `TaxRuleVersion`, ruleset ou implementação no `tax-engine`.

## Consequências

- A proveniência passa a ligar fonte legal, fonte técnica do catálogo, artefato, manifesto, hashes,
  staging, snapshot, itens e eventos.
- O banco pode ser reconstruído sem depender de volume efêmero, mas publicação continua exigindo
  atores segregados.
- O schema documental ganha referências adicionais; consumidores devem aceitar a nova versão do
  contrato.
- Ausência do artefato histórico oficial bloqueia somente as especificações que dependem dele; o
  snapshot atual não será usado como substituto silencioso.
- Fontes compiladas podem mudar no portal oficial; alteração de bytes produz novo hash e exige nova
  curadoria em vez de sobrescrever a fonte anterior.

## Alternativas consideradas

1. **INSERTs SQL e IDs escolhidos manualmente:** rejeitada por quebrar services, auditoria,
   idempotência e rastreabilidade.
2. **Seed normativo dentro da migração:** rejeitada porque mistura schema e conteúdo oficial e
   dificulta revisão humana.
3. **Usar somente a LC 214 compilada como fonte genérica:** rejeitada porque ocultaria atos
   alteradores e fundamentos complementares.
4. **Usar o catálogo atual na regra histórica:** rejeitada por violar temporalidade e reprodução.
5. **Criar coluna adicional `fingerprint`:** rejeitada neste momento porque `normalized_hash` já
   representa exatamente o fingerprint canônico do snapshot normalizado.

## Critérios de revisão

Revisar antes de tornar o catálogo global entre organizações, automatizar publicação, aceitar
domínios oficiais adicionais, adotar assinatura digital externa, mudar a definição do
`normalized_hash` ou permitir atualização de fonte compilada sem nova versão governada.
