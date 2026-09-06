# Etapa 9.2 — relatório de arquitetura, transição e Imposto Seletivo

## Transição

Períodos modeláveis: 2026, 2027, 2028, 2029, 2030, 2031, 2032 e 2033 em diante. O contrato
`TaxTransitionPeriod` carrega versão, vigência, fonte, dispositivo e hash. Nenhum período foi
persistido ou publicado como regra produtiva.

## Interações

Relações confirmadas documentalmente:

- IBS/CBS excluem os próprios tributos de sua base;
- ICMS, ISS, PIS e Cofins são excluídos da base de IBS/CBS no intervalo legal até 2032;
- o IS integra a base de IBS/CBS;
- na importação, II e IS integram a base de IBS/CBS, enquanto IPI, ICMS e ISS são excluídos;
- CBS, IBS e o próprio IS são excluídos da base do IS;
- ICMS e ISS são excluídos da base do IS até 2032.

Relações pendentes: demais componentes da base do IS e os efeitos de IBS/CBS/IS nas bases de ICMS
e ISS conforme suas legislações próprias. Pendente não significa incluído nem excluído.

## Imposto Seletivo

`IS` passou a ser `TaxDomain`, separado de cClassTrib e do cálculo IBS/CBS. Incidência,
não incidência, base, alíquota, incidência única, importação, exportação, devolução/créditos, fatos,
vigência e fontes necessárias estão mapeados. Não há regra, alíquota ou cálculo de IS executável.

## ICMS e ISS

Há roadmaps nacionais de transição, sem tentativa de reproduzir a legislação das 27 UFs ou de todos
os municípios. As frações constitucionais anuais não são tratadas como alíquotas nominais.

## Cálculo e auditoria

Foram criados `TaxComputationResult`, `CalculationTrace`, `TaxInteractionRule`,
`TaxTransitionPeriod`, `TaxDomain` e contratos auxiliares. `CalculationTrace` demonstra a
transformação monetária; `DecisionTrace` continua explicando o enquadramento. Valores usam
`TaxDecimal`, e ausência de regra produz `REQUIRES_VALIDATION` com valor ausente.

O contrato futuro de `/planejamento/transicao` e a operação sintética de R$ 100.000,00 demonstram
somente estrutura. Bases, alíquotas, valores e carga total permanecem nulos.

## Bloqueadores

- leis/atos de alíquotas e parâmetros governados para cada domínio;
- regras de interação aprovadas e publicadas por período;
- fontes estaduais de ICMS e municipais de ISS;
- especificações por família do IS, incluindo classificadores e fatos técnicos;
- persistência e publicação bitemporal dos novos contratos;
- revisão jurídica, testes e rulesets antes de qualquer cálculo.

## Garantias do fechamento

Nenhuma regra fiscal fictícia foi criada ou publicada. A `RT-IBSCBS-0003` não foi modificada e
permanece a única regra real do ruleset piloto; sua reprodução será conferida na suíte completa.

## Próxima etapa recomendada

Governar e revisar juridicamente as primeiras regras de interação e os períodos normativos, sem
interromper o saneamento das `RT-IBSCBS-0007` a `0009`. Implementação financeira ampla depende de
nova autorização.
