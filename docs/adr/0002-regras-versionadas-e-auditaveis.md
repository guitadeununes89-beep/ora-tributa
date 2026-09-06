# ADR-0002 — Regras imutáveis, temporalidade e proveniência

- **Status:** Aceita
- **Data:** 2026-08-29

## Contexto

Legislação muda, pode produzir efeitos retroativos e pode ser corrigida no sistema depois. Sobrescrever registros impede reproduzir cálculos históricos.

## Decisão

Cada regra terá identidade lógica e versões imutáveis. A solução distinguirá vigência jurídica de tempo de registro no sistema (abordagem bitemporal a detalhar). Toda versão terá fonte e fundamento legal. Cada avaliação persistirá referências exatas ao motor e às versões usadas.

## Consequências

Será possível reproduzir e auditar resultados históricos. Consultas e curadoria ficam mais complexas; será necessário workflow de publicação, constraints temporais e estratégia de correção.

## Alternativas consideradas

- Atualizar regra vigente no lugar: rejeitada por destruir evidência histórica.
- Guardar apenas snapshots de resultados: rejeitada porque não explica a decisão nem permite reprocessamento confiável.

## Critérios de revisão

O modelo físico será detalhado antes da primeira migração de regras, sem enfraquecer a imutabilidade.

