# Contrato futuro — planejamento da transição

## Estado

**Somente especificação.** Não existe rota, caso de uso produtivo ou cálculo associado. A URL futura
é `/planejamento/transicao`; sua eventual API deverá permanecer versionada sob `/api/v1`.

## Finalidade

Comparar uma mesma operação em datas distintas com as regras que eram juridicamente vigentes e as
versões conhecidas pelo sistema em cada avaliação. O contrato não aceita percentuais definidos pelo
frontend e não transforma lacunas em zero.

## Entrada conceitual

| Campo | Tipo lógico | Regra |
|---|---|---|
| `operation` | objeto normalizado | fatos necessários à classificação e ao cálculo, sem documento fiscal completo |
| `operation.value` | decimal em string | obrigatório; JSON number/float proibido |
| `operation.date` | data ISO | cenário-base |
| `comparison_dates` | lista de datas ISO | cenários pedidos pelo usuário; não ficam fixos na tela |
| `known_at` | instante com timezone | corte bitemporal para reprodução |
| `organization_id` | identificador | isolamento e autorização no backend futuro |
| `requested_taxes` | lista de `TaxDomain` | IBS, CBS, IS, ICMS e/ou ISS; expansão explícita |
| `ruleset_selector` | referência governada | nunca “último” implícito em reprodução histórica |

## Saída conceitual

Cada cenário contém:

- data e `TaxTransitionPeriod` exato;
- hash da operação e fingerprint do ruleset;
- resultado de classificação com `DecisionTrace`, quando aplicável;
- um `TaxComputationResult` por tributo solicitado;
- base, alíquota nominal, alíquota efetiva, redução, adições, exclusões, valor e crédito;
- fontes legais e versões de regras;
- `CalculationTrace` ordenada;
- pendências e fatos ausentes;
- total apenas quando todos os componentes necessários forem calculáveis.

## Estados

- `CALCULATED`: todos os elementos necessários existem e são rastreados;
- `REQUIRES_VALIDATION`: falta regra, fonte, alíquota, interação ou fato;
- `NOT_APPLICABLE`: uma regra publicada determinou não aplicabilidade; não é sinônimo de ausência.

Um `REQUIRES_VALIDATION` possui `amount: null`. O sistema não retorna `"0.00"` como fallback.

## Comparação temporal

O backend futuro resolve as datas contra períodos governados e executa cada cenário de forma
independente. A comparação mostra a diferença somente entre valores calculáveis; cenários
incompletos são comparados por estado e pendências, não por aritmética fictícia.

## Exemplo não normativo

O arquivo [`examples/TEST-TAX-TRANSITION-100000.json`](examples/TEST-TAX-TRANSITION-100000.json)
usa uma operação sintética de R$ 100.000,00. Todos os campos normativos permanecem `null` e todos os
tributos ficam em `REQUIRES_VALIDATION`; o exemplo valida apenas forma, precisão e transparência.
