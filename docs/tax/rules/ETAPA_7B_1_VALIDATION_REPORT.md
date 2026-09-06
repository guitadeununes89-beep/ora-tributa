# Relatório final — Etapa 7B.1

## Resultado executivo

- seis especificações reais permanecem em `DRAFT`;
- nenhuma possui `implementation` ou autorização para publicação;
- 16 testes automatizados passaram;
- o preflight estrutural controlado retorna `NOT_READY — STATUS_NOT_APPROVED` para todas;
- o comando real retorna `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` porque o PostgreSQL local não
  está disponível;
- nenhum ID governado foi inventado ou vinculado sem consulta ao banco.

## Alterações realizadas

### RT-IBSCBS-0001 — art. 133, § 2º

A especificação passou à versão documental 2 e deixou de usar
`supplier.art_133_price_condition`. Agora distingue:

- fornecedor da operação;
- fabricante do medicamento;
- importador responsável;
- papel da pessoa jurídica juridicamente responsável pelo requisito do § 2º;
- condição de preço atribuída somente após validação dessa entidade.

O bloqueador `NEEDS_LEGAL_VALIDATION_ART133_RESPONSIBLE_ENTITY` impede seleção automática da
entidade. A especificação também exige `operation.art_146_coverage_status = COMPLETE` antes de
aceitar um resultado agregado `NOT_ELIGIBLE` do art. 146.

### RT-IBSCBS-0002 — lista do § 3º

A especificação passou à versão documental 2. A modelagem conservadora foi preservada e o bloqueador
`NEEDS_ART146_PAR3_OFFICIAL_LIST` foi registrado. A pesquisa oficial não localizou com segurança ato
conjunto vigente contendo a lista; o requisito não foi removido nem inferido.

### RT-IBSCBS-0003 — art. 146, § 1º, I

A especificação passou à versão documental 2. O escopo jurídico do inciso I foi registrado como
aceito pela revisão humana. A cClassTrib `200010` também atende ao inciso II no catálogo oficial,
mas as regras permanecem separadas e deverão produzir fundamentos próprios na `DecisionTrace`.

### Novas especificações

- `RT-IBSCBS-0004`: redação histórica do caput e Anexo XIV, de 01/01/2026 a 13/01/2026; CST `200`,
  cClassTrib `200009`, conforme catálogo oficial publicado em 15/12/2025;
- `RT-IBSCBS-0005`: art. 146, § 1º, II, com CST `200` e cClassTrib `200010`;
- `RT-IBSCBS-0006`: art. 146, § 1º, III, com CST `200` e cClassTrib `200053`, bloqueada por
  `NEEDS_OFFICIAL_SANITARY_REGULATION` e `NEEDS_ART146_PAR3_OFFICIAL_LIST`.

`RT-IBSCBS-0007` foi identificada como especificação futura necessária para o § 2º. A hipótese do
§ 4º exigirá especificação temporal por ato e emergência; `RT-IBSCBS-0008` é apenas uma reserva
conceitual na matriz de cobertura. Nenhum desses dois arquivos foi criado.

## Cobertura do art. 146

A cobertura completa está em `ART146_COVERAGE_MATRIX.md` e separa:

- redação original, de 01/01/2026 a 13/01/2026;
- redação da LC nº 227/2026, desde 14/01/2026;
- caput/incisos I–VII, §§ 1º I–III, 2º, 3º e 4º;
- regras existentes, lacunas e bloqueadores.

Enquanto houver linha aplicável em `LACUNA`, `BLOQUEADOR`, `INCOMPLETE` ou `UNKNOWN`, a
`RT-IBSCBS-0001` não pode concluir ausência de alíquota zero.

## Resultado atualizado do preflight

| Regra | Versão | Status | Validação estrutural controlada | Comando real |
|---|---:|---|---|---|
| RT-IBSCBS-0001 | 2 | `DRAFT` | `NOT_READY — STATUS_NOT_APPROVED` | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |
| RT-IBSCBS-0002 | 2 | `DRAFT` | `NOT_READY — STATUS_NOT_APPROVED` | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |
| RT-IBSCBS-0003 | 2 | `DRAFT` | `NOT_READY — STATUS_NOT_APPROVED` | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |
| RT-IBSCBS-0004 | 1 | `DRAFT` | `NOT_READY — STATUS_NOT_APPROVED` | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |
| RT-IBSCBS-0005 | 1 | `DRAFT` | `NOT_READY — STATUS_NOT_APPROVED` | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |
| RT-IBSCBS-0006 | 1 | `DRAFT` | `NOT_READY — STATUS_NOT_APPROVED` | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |

### Problemas estruturais

Nenhum problema de schema, temporalidade, fatos, precedência, códigos ou grupos de casos foi
encontrado na validação controlada. Os 16 testes direcionados passaram.

### Problemas de infraestrutura e referências

O host não possui PostgreSQL, Docker, `psql` ou backend em execução. Por isso não foi possível
aplicar migrações nem consultar as tabelas governadas. O comando foi repetido para os seis arquivos
e falhou fechado com `REFERENCE_LOOKUP_UNAVAILABLE`.

## IDs governados

Nenhum ID foi vinculado. Permanecem pendentes:

- `PENDING-LC214-2025-COMPILED`;
- `PENDING-LC214-2025-ORIGINAL`;
- `PENDING-PUBLISHED-CATALOG-1448CB63A41B`;
- `PENDING-GOVERNED-CATALOG-2025-12-15`.

Essas strings são marcadores documentais, não IDs governados. O repositório possui o artefato atual
e o manifesto, mas não uma exportação confiável dos IDs persistidos. A orientação de não criar IDs
manualmente foi preservada.

## Bloqueadores jurídicos restantes

| Regra | Bloqueadores principais |
|---|---|
| RT-IBSCBS-0001 | definição da entidade do art. 133, § 2º; cobertura completa do art. 146; IDs governados; aprovação |
| RT-IBSCBS-0002 | lista oficial do § 3º; natureza jurídica da lista; vocabulário; IDs; aprovação |
| RT-IBSCBS-0003 | IDs governados; autoria, revisão e evidência de aprovação |
| RT-IBSCBS-0004 | fonte e catálogo histórico governados; conferência temporal do Anexo XIV; aprovação |
| RT-IBSCBS-0005 | evidências canônicas de imunidade, CEBAS, SUS e adquirente efetivo; IDs; aprovação |
| RT-IBSCBS-0006 | regulamentação sanitária específica; lista do § 3º; IDs; aprovação |

## Proximidade jurídica de aprovação

`RT-IBSCBS-0003` é a mais próxima no mérito jurídico, pois o recorte do inciso I foi aceito. Ainda
assim, não pode ser promovida sem fonte e catálogo governados e sem autoria, revisão e evidência de
aprovação. `RT-IBSCBS-0004` possui hipótese e período delimitados, mas depende da governança da fonte,
do catálogo histórico e da conferência do Anexo XIV. As demais possuem bloqueadores jurídicos
materiais adicionais.

## Confirmação de não execução

Nenhuma `TaxRuleVersion` brasileira real foi criada. Nenhum ruleset brasileiro real foi publicado.
Nenhuma das seis especificações está incorporada ou executável pelo `tax-engine`.
