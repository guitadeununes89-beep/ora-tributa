# ADR-0010 — Publicação atômica e imutável de rulesets

- **Status:** Aceita
- **Data:** 2026-08-29
- **Relacionados:** ADR-0007, ADR-0008 e ADR-0009

## Contexto

Uma avaliação não pode observar metade de uma publicação nem depender de uma consulta implícita às
“regras atuais”. O conjunto exato precisa ser identificado, verificável e recuperável no futuro.

## Decisão

Um ruleset nasce `DRAFT` com uma lista explícita e sem duplicidade de `TaxRuleVersion`. Sua
publicação executa, em uma única transação PostgreSQL:

1. lock do ruleset e das versões referenciadas;
2. validação de que todas as versões estão `PUBLISHED`;
3. cálculo SHA-256 canônico da identidade, versão e hash de cada membro, ordenados;
4. atualização do ruleset para `PUBLISHED`, com ator, instante e fingerprint;
5. inclusão do evento `RULESET_PUBLISHED`.

Qualquer falha desfaz toda a transação. Depois da publicação, cabeçalho e itens são imutáveis por
serviço e por trigger. O adaptador resolve o snapshot em objetos `RuleSet` e implementações
executáveis allowlisted. Conteúdo persistido nunca é executado com `eval` ou import dinâmico.

O fingerprint persistido é verificado novamente no carregamento. Divergência impede avaliação. A
avaliação grava o fingerprint e as versões usadas, permitindo reprodução sem consultar um
“ruleset mais recente”.

## Alternativas consideradas

- **Ruleset como consulta dinâmica:** rejeitado por não ser reproduzível.
- **Publicar cada item separadamente:** rejeitado por permitir visibilidade parcial.
- **Permitir editar e recalcular o hash:** rejeitado porque destrói a identidade do snapshot.
- **Serializar código Python no banco:** rejeitado por risco de execução e baixa governança.

## Consequências

Correções exigem outro ruleset. A publicação pode gerar contenção breve devido aos locks, aceitável
para um fluxo administrativo. Novas implementações executáveis precisam de registro explícito e
teste no backend.

## Critérios de revisão

Revisar se o catálogo exigir publicação distribuída, assinatura criptográfica externa ou promoção
do mesmo snapshot entre ambientes.

