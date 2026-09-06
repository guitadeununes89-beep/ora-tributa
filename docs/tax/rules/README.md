# Especificações jurídicas executáveis

Este diretório governa a preparação documental de regras tributárias. Não existe aqui, nesta data,
nenhuma especificação brasileira real `APPROVED`; portanto nenhuma regra real está autorizada para
implementação ou execução.

## Artefatos

- `PILOT_RULES_MATRIX.md`: reserva RT-IBSCBS-0001 a RT-IBSCBS-0005 sem conteúdo tributário;
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

Os endpoints atuais de criação de regras continuam restritos a conteúdo `TEST-*`, fonte
`example.invalid` e implementação `SYNTHETIC_*`. A primeira regra real exigirá nova etapa para
persistir a proveniência obrigatória e registrar um adaptador allowlisted revisado.

## Proibições

- não mover fixtures `TEST-*` para `specifications/`;
- não preencher a matriz sem orientação jurídica;
- não inferir NCM para CST/cClassTrib;
- não copiar descrição oficial como fonte de verdade;
- não tratar `READY_FOR_IMPLEMENTATION` como aprovação jurídica;
- não gerar implementação automaticamente do JSON.
## Etapa 7B.1

O saneamento jurídico intermediário está documentado em:

- `ART146_COVERAGE_MATRIX.md`;
- `ETAPA_7B_1_PESQUISA_OFICIAL.md`;
- `ETAPA_7B_1_VALIDATION_REPORT.md`.

As especificações `RT-IBSCBS-0001` a `RT-IBSCBS-0006` permanecem em `DRAFT`. Os IDs 0007 e 0008
aparecem somente como necessidades futuras na matriz de cobertura e não correspondem a arquivos
criados. Ausência de PostgreSQL ou de vínculo governado nunca pode ser compensada por ID manual.
Nenhum documento desta etapa autoriza `TaxRuleVersion`, ruleset brasileiro ou execução pelo
`tax-engine`.
