# Especificações jurídicas executáveis

Este diretório governa a preparação documental de regras tributárias. Somente
`RT-IBSCBS-0003` versão 2 está `APPROVED`, possui mapeamento de implementação e autoriza a regra
piloto publicada descrita no relatório da Etapa 7C. `RT-IBSCBS-0001`, `0002`, `0004`, `0005` e
`0006` permanecem `DRAFT` e não autorizam implementação ou execução. A Etapa 9 acrescentou
`RT-IBSCBS-0007`, `RT-IBSCBS-0008` e `RT-IBSCBS-0009`, também exclusivamente `DRAFT`, para o
bloco documental de operações com bens na ZFM e em ALC.

## Artefatos

- `PILOT_RULES_MATRIX.md`: acompanha o bloco inicial RT-IBSCBS-0001 a RT-IBSCBS-0006;
- `../../ETAPA_9_P1_SELECTION.md`: registra a comparação P1 e a seleção de RT-IBSCBS-0007 a 0009;
- `../../ETAPA_9_1_P1_LEGAL_REVIEW.md`: consolida a revisão oficial e a classificação A/B/C;
- `../RT-IBSCBS-0009_LEGAL_DISCREPANCY_REPORT.md`: preserva o conflito literal de 200024;
- `../FAMILY_LEGAL_REVIEW_PIPELINE.md`: define o fluxo reutilizável dos próximos lotes;
- `specifications/<rule_id>.json`: localização exclusiva das especificações reais canônicas;
- `../RULE_SPECIFICATION_TEMPLATE.json`: estrutura inicial intencionalmente `NOT_READY`;
- `../RULE_SPECIFICATION_TEMPLATE.md`: instruções completas de preenchimento;
- `../examples/TEST-IBSCBS-0001.json`: fixture fictícia fora do diretório real.

## Lifecycle

```text
DRAFT → IN_REVIEW → APPROVED → IMPLEMENTED → SUPERSEDED
```

Somente `APPROVED` pode retornar `READY_FOR_IMPLEMENTATION`. `IMPLEMENTED` deve registrar a
`TaxRuleIdentity` e a `TaxRuleVersion` correspondentes. Versões aprovadas não são sobrescritas;
alterações materiais criam nova versão documental. O Git preserva revisão e histórico nesta etapa.

## Pre-flight obrigatório

```bash
uv run validate-tax-rule-spec docs/tax/rules/specifications/RT-IBSCBS-0001.json \
  --organization-id <organization_id>
```

O processo verifica:

1. schema e campos obrigatórios;
2. status e metadados de aprovação;
3. fonte normativa cadastrada no tenant;
4. snapshot exato e `PUBLISHED` do catálogo;
5. CST, cClassTrib e sua relação estrutural;
6. vigência e coerência do resultado;
7. casos positivos, negativos, inconclusivos e de limite temporal;
8. fundamento explícito para qualquer precedência.

`READY_FOR_IMPLEMENTATION` significa apenas que a estrutura e as referências governadas estão
completas. Não valida interpretação jurídica, não publica regra e não gera código.

## Fluxo sem atalhos

```text
Especificação jurídica
  → validação estrutural
  → revisão jurídica
  → APPROVED
  → TaxRuleIdentity
  → TaxRuleVersion com proveniência da especificação
  → testes associados
  → revisão técnica
  → PUBLISHED
  → ruleset publicado
  → motor determinístico
```

A criação governada aceita regras reais somente pelo fluxo especializado, com especificação
`APPROVED`, proveniência persistida e implementação allowlisted. O registro real contém apenas
`REAL_RT_IBSCBS_0003_V1`; fixtures `TEST-*` e `SYNTHETIC_*` continuam isoladas.

## Proibições

- não mover fixtures `TEST-*` para `specifications/`;
- não inferir NCM para CST/cClassTrib;
- não copiar descrição oficial como fonte de verdade;
- não tratar `READY_FOR_IMPLEMENTATION` como aprovação jurídica;
- não gerar implementação automaticamente do JSON.



