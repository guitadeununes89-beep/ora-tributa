# Roadmap consolidado do motor tributário

## Objetivo

Coordenar três eixos independentes que convergem somente por contratos e regras de interação
versionadas. Progresso em um eixo não autoriza inferência nos demais.

## Eixo A — cobertura IBS/CBS

- ampliar especificações por família oficial;
- concluir revisão jurídica, aprovação humana, implementação e publicação;
- preservar os quatro estados de classificação e `DecisionTrace`;
- evoluir de classificação para cálculo apenas após regras próprias de base, alíquota, crédito e
  arredondamento.

Referência: [`IBSCBS_COVERAGE_ROADMAP.md`](IBSCBS_COVERAGE_ROADMAP.md).

## Eixo B — Imposto Seletivo

- governar categorias e fontes do Anexo XVII;
- separar incidência/classificação de cálculo;
- aguardar e governar leis de alíquotas e atos técnicos aplicáveis;
- implementar por família, com `DecisionTrace` e `CalculationTrace`.

Referência: [`IMPOSTO_SELETIVO_COVERAGE_ROADMAP.md`](IMPOSTO_SELETIVO_COVERAGE_ROADMAP.md).

## Eixo C — transição e planejamento 2026–2033

- governar `TaxTransitionPeriod` e `TaxInteractionRule`;
- incorporar gradualmente ICMS e ISS sem apagar histórico;
- resolver bases, alíquotas, reduções, créditos e precedência por tributo;
- implementar cenários e comparação temporal somente após contratos e rulesets publicados.

Referências: [`TAX_TRANSITION_2026_2033_MATRIX.md`](TAX_TRANSITION_2026_2033_MATRIX.md),
[`ICMS_TRANSITION_ROADMAP.md`](ICMS_TRANSITION_ROADMAP.md) e
[`ISS_TRANSITION_ROADMAP.md`](ISS_TRANSITION_ROADMAP.md).

## Portões comuns

`FONTE OFICIAL → ESPECIFICAÇÃO → REVISÃO JURÍDICA → APROVAÇÃO HUMANA → IMPLEMENTAÇÃO → TESTES →`
`PUBLICAÇÃO → MONITORAMENTO`

Toda interação entre eixos percorre os mesmos portões. Uma base legal identificada não equivale a
regra executável, uma DRAFT não equivale a cobertura e ausência de regra não equivale a zero.

## Estado em 2026-09-03

- IBS/CBS: `RT-IBSCBS-0003` permanece a única regra real publicada, restrita ao ruleset piloto;
- IS: zero regras executáveis;
- ICMS: zero regras executáveis;
- ISS: zero regras executáveis;
- transição/cálculo: contratos de segurança e documentação, sem simulação tributária produtiva.
