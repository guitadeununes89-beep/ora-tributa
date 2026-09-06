# ADR-0023 — Motor de transição e interação tributária

- **Status:** Aceita
- **Data:** 2026-09-02
- **Escopo:** tax-engine, contratos futuros de planejamento e documentação normativa

## Contexto

A transição da Reforma Tributária entre 2026 e 2033 exige representar a coexistência de IBS, CBS,
Imposto Seletivo, ICMS e ISS sem acoplar o motor a uma tela, API ou calendário codificado no
frontend. A Constituição e a legislação complementar também estabelecem interações entre bases
tributáveis que variam por tributo, operação e vigência. Classificação fiscal, apuração de base,
aplicação de alíquota, cálculo de valor e crédito são decisões distintas e precisam ser auditáveis.

Não existe, nesta etapa, autorização para publicar novas regras nem para preencher alíquotas ou
lacunas normativas por inferência.

## Decisão

1. O núcleo reconhece os domínios `IBS`, `CBS`, `IS`, `ICMS` e `ISS`; `IPI`, `PIS`, `COFINS` e
   `ICMS_ST` são identificadores reservados para evolução, sem regra executável implícita.
2. `TaxTransitionPeriod` representa um período normativo versionado, com vigência, fonte,
   dispositivo e hash. Anos e percentuais não serão codificados na interface.
3. Cada interação de base será uma `TaxInteractionRule` versionada. Um tributo não importa nem
   chama diretamente a implementação de outro: um orquestrador futuro montará um grafo explícito
   das regras aplicáveis ao cenário.
4. Classificação permanece registrada em `DecisionTrace`. Cálculo usa `CalculationTrace`, com
   valores decimais, etapas ordenadas, versões e fontes próprias. Uma trilha pode referenciar a
   outra, mas nenhuma substitui a outra.
5. `TaxComputationResult` não presume que um tributo seja devido. Sem regra, alíquota, fato ou
   interação necessária, o estado é `REQUIRES_VALIDATION`, o valor calculado permanece ausente e a
   pendência é registrada. Zero só poderá existir como resultado de regra válida e rastreada.
6. Valores monetários, bases, alíquotas, reduções e créditos usam `TaxDecimal`/`Decimal`; `float` é
   proibido. Arredondamento continuará definido pela regra aplicável, nunca globalmente.
7. Reprocessamento requer data da operação, período de transição, fingerprint do ruleset, versões
   de regras, hash da entrada e etapas canônicas. Alteração normativa cria nova versão e preserva o
   resultado histórico.
8. O contrato futuro de `/planejamento/transicao` será especificado antes da rota. Nesta etapa ele
   aceita cenários e devolve estrutura auditável, mas não calcula tributos reais.
9. O Imposto Seletivo é domínio autônomo. A identificação de incidência e a classificação do objeto
   não autorizam, por si, cálculo de base, alíquota ou valor.

## Fluxo conceitual

`operação → classificação/aplicabilidade → período normativo → grafo de interações → base →`
`alíquota → valor → crédito → consolidação → CalculationTrace`

Cada seta depende de contrato e regra versionada. Uma etapa ausente interrompe a conclusão e deixa
uma pendência reproduzível.

## Consequências

- O motor permanece independente de FastAPI, SQLAlchemy, clientes HTTP e frontend.
- Comparações 2026–2033 podem evoluir por dados/regras versionados, sem alterar componentes visuais.
- Interações como inclusão ou exclusão de outro tributo na base ficam explícitas e temporalmente
  testáveis.
- O modelo aceita múltiplos resultados por operação e não soma valores incompletos.
- A implementação produtiva futura exigirá persistência governada, regras jurídicas aprovadas,
  testes e publicação de ruleset específico.
- Há custo adicional de orquestração e de armazenamento das trilhas, considerado necessário para
  auditoria e reprodução.

## Alternativas consideradas

- **Tabela anual no frontend:** rejeitada por duplicar norma, impedir governança e comprometer a
  reprodução histórica.
- **Um único cálculo monolítico para todos os tributos:** rejeitado por acoplamento e dificuldade de
  versionar interações.
- **Reutilizar somente `DecisionTrace`:** rejeitado porque a decisão de enquadramento não demonstra
  transformações monetárias.
- **Retornar zero quando faltar regra:** rejeitado por produzir conclusão fiscal silenciosa e falsa.
- **Usar alíquotas exemplificativas como fallback:** rejeitado por violar a proibição de inventar
  regra tributária.

## Limites desta decisão

Este ADR aprova contratos de segurança e documentação. Não aprova alíquotas, regras de incidência,
créditos, arredondamentos, calendários executáveis nem publicação de regras reais.
