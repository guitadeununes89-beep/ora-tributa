# ADR-0007 — Temporalidade bitemporal das regras tributárias

- **Status:** Aceita
- **Data:** 2026-08-29
- **Relacionados:** ADR-0002 e ADR-0006

## Contexto

Uma norma pode produzir efeitos jurídicos em período diferente daquele em que foi cadastrada, revisada e publicada na plataforma. Também pode ser conhecida tardiamente ou substituída depois de já ter participado de avaliações. Uma única coluna de vigência ou um estado `active` não permite responder simultaneamente qual regra valia para o fato e qual versão o sistema conhecia quando calculou.

## Decisão

Adotar duas dimensões temporais explícitas:

1. **Tempo jurídico:** `valid_from` inclusivo e `valid_to` exclusivo, formando o intervalo semiaberto `[valid_from, valid_to)`. `valid_to = null` representa ausência de término conhecido.
2. **Tempo do sistema:** `recorded_at` no snapshot e eventos append-only do lifecycle, dos quais são derivados `approved_at`, `published_at` e `superseded_at` quando existirem.

Os timestamps derivados não serão duplicados como fonte de verdade na versão da regra. A sequência de eventos é a fonte auditável do estado no sistema. Projeções de leitura poderão materializá-los futuramente, desde que possam ser reconstruídas.

Toda avaliação informará separadamente:

- `operation_date`: data jurídica do fato contida no `FactSet`;
- `known_at`: instante do conhecimento do sistema usado para selecionar versões;
- `evaluated_at`: instante em que a execução ocorreu.

Uma versão somente entra na avaliação determinística se estava `PUBLISHED` em `known_at` e se `operation_date` pertence ao seu intervalo jurídico. Versões posteriormente `SUPERSEDED` continuam reproduzíveis quando o `known_at` histórico antecede a supersessão.

A avaliação registrará a versão do motor, a referência imutável do ruleset, os hashes de entrada/ruleset e as versões efetivamente avaliadas. Reproduzir significa usar novamente os mesmos fatos canônicos, `known_at`, versão do motor e ruleset imutável; `evaluation_id`, `evaluated_at` e `correlation_id` são metadados de execução e não alteram a decisão.

## Persistência futura

O schema definitivo deverá preservar snapshots e eventos, impor unicidade por identidade/versão e usar timestamps com timezone para tempo do sistema. Consultas temporais deverão receber as duas dimensões explicitamente. Nenhuma tabela é criada por este ADR; constraints, índices, ranges PostgreSQL e política de correções retroativas exigirão ADR de modelo físico antes da primeira migração.

## Consequências

- avaliações históricas podem ser explicadas e reproduzidas;
- mudanças retroativas não apagam o que a plataforma sabia anteriormente;
- seleção de regra exige sempre uma data jurídica e um instante de conhecimento;
- consultas e persistência ficam mais complexas, mas sem ambiguidade temporal;
- o significado exclusivo de `valid_to` deve ser mantido em API, banco e testes.

## Alternativas consideradas

- **Apenas `valid_from/valid_to`:** rejeitada porque não representa quando a versão foi conhecida/publicada.
- **Apenas timestamps do sistema:** rejeitada porque não responde à vigência jurídica do fato.
- **Campos mutáveis `approved_at/published_at/superseded_at` na versão:** rejeitados como fonte primária por duplicarem e poderem divergir do histórico de eventos.
- **Usar o relógio atual implicitamente:** rejeitado porque impede reprodução determinística.

## Critérios de revisão

Revisar quando o modelo físico for especificado ou se uma fonte normativa exigir semântica de intervalo diferente. A separação entre tempo jurídico e tempo do sistema não pode ser removida.

