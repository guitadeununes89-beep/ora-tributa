# ADR-0022 — Projeção de prontidão jurídica na cobertura

- **Estado:** Aceito
- **Data:** 2026-09-02
- **Relacionados:** ADR-0006, ADR-0015, ADR-0018 e ADR-0020

## Contexto

A cobertura precisa distinguir DRAFT pronto para revisão humana de DRAFT bloqueado. Prontidão é
resultado de validação, não estado do lifecycle.

## Decisão

1. A API acrescentará `review_readiness`, projeção derivada e não persistida.
2. Será `READY_FOR_HUMAN_REVIEW` com especificação DRAFT, sem bloqueador e sem implementação;
   `BLOCKED` com bloqueador; `NOT_APPLICABLE` nos demais casos.
3. `ready_for_review` será contado por cClassTrib distinto.
4. A projeção não altera status, não equivale a aprovação e não aumenta cobertura executável.
5. A mudança do contrato é aditiva.

## Consequências

A interface evidencia o gate humano sem promover documentos e sem pressupor relação 1:1 entre regra
e cClassTrib.

## Alternativas consideradas

Novo lifecycle `READY` e rótulo persistido foram rejeitados por misturar estado e avaliação.

## Critérios de revisão

Revisar quando pareceres persistidos ou múltiplas revisões forem exigidos.
