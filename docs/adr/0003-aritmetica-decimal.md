# ADR-0003 — Aritmética decimal e contratos monetários

- **Status:** Aceita
- **Data:** 2026-08-29

## Contexto

Ponto flutuante binário não representa com exatidão muitos valores decimais e pode introduzir divergências em cálculos fiscais.

## Decisão

Usar `Decimal` no domínio Python e `NUMERIC` no PostgreSQL. Valores monetários e percentuais cruzarão JSON em representação decimal por string até que contratos específicos definam tipos mais restritos. Arredondamento será sempre explícito e vinculado à regra aplicável.

## Consequências

Evita erros binários e torna a memória de cálculo reproduzível. Serialização e frontend exigem cuidados; conversões para `number` ficam proibidas em fluxos fiscais.

## Alternativas consideradas

- `float`/JSON number: rejeitado por perda de precisão.
- Inteiros em centavos globalmente: insuficiente para alíquotas, bases e escalas variáveis.

## Critérios de revisão

Reavaliar apenas representação de transporte/armazenamento por caso; a proibição de ponto flutuante permanece.

