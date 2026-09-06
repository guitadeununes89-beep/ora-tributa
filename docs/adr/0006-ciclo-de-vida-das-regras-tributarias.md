# ADR-0006 — Ciclo de vida das regras tributárias

- **Status:** Aceita
- **Data:** 2026-08-29
- **Substitui:** detalha o workflow deixado em aberto pelo ADR-0002

## Contexto

Uma regra tributária precisa passar por elaboração, revisão jurídica, aprovação e publicação antes de poder participar de uma avaliação. Além disso, a vigência jurídica de uma norma não coincide necessariamente com o momento em que a plataforma tomou conhecimento dela. Tratar esses conceitos como um único campo `ativo` impediria reproduzir resultados históricos e permitiria que rascunhos ou regras ainda não aprovadas fossem executados.

A plataforma também precisa corrigir erros editoriais ou acompanhar mudanças legislativas sem sobrescrever conteúdo anteriormente usado. O ciclo de vida deve, portanto, preservar tanto as versões do conteúdo quanto todas as mudanças de estado.

## Decisão

Adotar um ciclo de vida explícito, determinístico e orientado a eventos append-only para cada versão de regra.

### Identidade e conteúdo

- `rule_id` identifica de forma estável a regra lógica.
- `version` identifica um snapshot imutável de seu conteúdo.
- O conteúdo de uma versão é identificado por hash criptográfico; alterar conteúdo exige criar outra versão, nunca editar o snapshot existente.
- O estado atual não será sobrescrito como fonte de verdade: será derivado da sequência ordenada de eventos de ciclo de vida.

### Estados

- `DRAFT`: snapshot cadastrado, ainda não submetido à revisão e inelegível para cálculo.
- `IN_REVIEW`: submetido à revisão técnico-jurídica e inelegível para cálculo.
- `APPROVED`: aprovado, mas ainda não publicado no conjunto executável.
- `PUBLISHED`: publicado e potencialmente elegível, condicionado às dimensões temporais e ao contexto da avaliação.
- `REJECTED`: revisão encerrada sem aprovação; terminal e inelegível.
- `SUPERSEDED`: versão publicada substituída por versão posterior identificada; permanece histórica.
- `WITHDRAWN`: versão publicada retirada de novas avaliações por decisão excepcional fundamentada; permanece histórica.

### Transições permitidas

- `DRAFT → IN_REVIEW`
- `IN_REVIEW → APPROVED`
- `IN_REVIEW → REJECTED`
- `APPROVED → PUBLISHED`
- `PUBLISHED → SUPERSEDED`
- `PUBLISHED → WITHDRAWN`

Qualquer outra transição é inválida. Mudança solicitada durante a revisão ou após aprovação gera novo snapshot/versionamento, em vez de reabrir e alterar o conteúdo existente.

### Eventos e auditoria

Cada transição gera um evento imutável contendo pelo menos: identificador do evento, regra e versão, estado anterior e posterior, instante com timezone, ator, justificativa e eventual versão relacionada. A cadeia de eventos deve ser contínua, cronológica e posterior ao registro do snapshot.

Rejeição e retirada exigem justificativa. Supersessão exige referência a uma versão numericamente posterior da mesma regra. Identidade humana, papéis, assinatura e segregação de funções serão validados pela camada de aplicação após ADR específico de autorização; o motor conserva os identificadores recebidos sem depender de autenticação.

### Aplicabilidade bitemporal

`PUBLISHED` não equivale, isoladamente, a “aplicável”. Uma versão só pode ser selecionada quando:

1. seu estado, no instante de conhecimento consultado (`known_at`), era `PUBLISHED`; e
2. a data do fato (`operation_date`) pertence ao intervalo jurídico semiaberto `[valid_from, valid_to)`; e
3. as demais condições determinísticas da regra forem satisfeitas futuramente.

O fim de vigência é exclusivo. Uma versão supersedida ou retirada continua reproduzível para avaliações cujo `known_at` anteceda o respectivo evento. Avaliações novas usam um conjunto de regras publicado e explicitamente versionado; não consultam “a regra atual” de forma implícita.

### Concorrência e persistência

A persistência futura deverá impor unicidade de `(rule_id, version)`, `event_id` e hash do snapshot conforme o modelo físico. O append de eventos usará controle otimista de concorrência para impedir duas transições concorrentes a partir do mesmo estado. Tabelas, constraints e índices serão definidos em migração somente após ADR do modelo físico.

## Consequências

### Positivas

- rascunhos e regras não aprovadas não entram silenciosamente no cálculo;
- qualquer estado histórico pode ser reconstruído;
- correções e mudanças legislativas preservam resultados anteriores;
- vigência jurídica e conhecimento do sistema permanecem separados;
- o motor pode testar transições e elegibilidade sem banco, API ou interface.

### Custos e riscos

- consultas temporais e publicação ficam mais complexas;
- o armazenamento terá mais eventos e snapshots;
- será necessário workflow operacional de revisão, papéis e segregação de funções;
- a publicação de conjuntos de regras exigirá outra decisão sobre hashing/assinatura e atomicidade.

## Alternativas consideradas

- **Campo booleano `active`:** rejeitado por misturar aprovação, publicação e vigência.
- **Atualizar o status e descartar o anterior:** rejeitado por destruir a trilha de auditoria.
- **Permitir edição até a publicação:** rejeitado porque o conteúdo revisado poderia divergir do conteúdo aprovado; cada alteração material deve produzir outro snapshot.
- **Usar somente vigência legal:** rejeitado porque não representa quando a plataforma conheceu ou publicou a versão.
- **Modelar o workflow apenas no banco/API:** rejeitado porque permitiria estados inválidos fora desses adaptadores e acoplaria um invariante do domínio à infraestrutura.

## Critérios de revisão

Revisar este ADR se requisitos jurídicos determinarem outro significado para intervalos de vigência, se houver necessidade formal de revogar aprovação antes da publicação ou quando forem definidos assinatura digital, papéis de aprovação e publicação atômica de conjuntos de regras.
