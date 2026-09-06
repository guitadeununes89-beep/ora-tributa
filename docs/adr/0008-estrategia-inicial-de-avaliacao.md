# ADR-0008 — Estratégia inicial de avaliação determinística

- **Status:** Aceita
- **Data:** 2026-08-29
- **Relacionados:** ADR-0001, ADR-0003, ADR-0006 e ADR-0007

## Contexto

É necessário validar a arquitetura do motor com regras fictícias sem antecipar uma DSL, sem codificar legislação brasileira e sem acoplar o domínio à API ou ao banco. A execução deve expor por que cada regra foi selecionada, quais condições foram satisfeitas e qual ruleset produziu o resultado.

## Decisão

Adotar inicialmente contratos Python pequenos e explícitos:

- `FactSet` representa fatos normalizados e extensíveis;
- `DeterministicRule` é um `Protocol` implementado por objetos Python imutáveis;
- cada regra aponta para uma `TaxRuleVersion` e seu `RuleLifecycle`;
- `RuleSet` é uma coleção ordenada e versionada, com fingerprint calculado das versões/hashes;
- `TaxEngine` primeiro filtra lifecycle e vigência, depois chama somente regras elegíveis;
- cada regra retorna `RuleDecision` e condições estruturadas, sem lançar conclusão arbitrária;
- a agregação produz `CONCLUSIVO`, `POSSIVEIS_ENQUADRAMENTOS`, `NECESSITA_VALIDACAO` ou `SEM_CLASSIFICACAO` e uma `DecisionTrace` completa.

Somente versões `PUBLISHED` em `known_at` e juridicamente vigentes em `operation_date` podem ter sua função de avaliação executada. Regras presentes no ruleset mas inelegíveis aparecem apenas na fase de seleção da trilha; elas não afetam a classificação.

A prioridade de agregação será:

1. qualquer regra elegível que dependa de fato ausente produz `NECESSITA_VALIDACAO`, pois uma conclusão concorrente pode estar oculta;
2. sem pendência, mais de um candidato distinto produz `POSSIVEIS_ENQUADRAMENTOS`;
3. exatamente um candidato distinto produz `CONCLUSIVO`;
4. nenhum candidato produz `SEM_CLASSIFICACAO`.

O motor não acessa relógio, rede, banco ou gerador de identificadores. `EvaluationContext` recebe todos os valores variáveis. O hash da entrada usa serialização JSON canônica e valores fiscais permanecem strings/decimais seguros.

Regras sintéticas do endpoint experimental ficarão identificadas em módulo próprio do backend. Elas não representam legislação, não são persistidas e não constituem catálogo tributário.

## DSL e mecanismos declarativos

Não será criada DSL nesta etapa. Uma representação declarativa poderá ser avaliada futuramente se a curadoria, explicabilidade, validação estática e volume de regras justificarem. Qualquer adoção exigirá ADR, threat model e estratégia de versionamento do interpretador.

## Consequências

- o motor permanece testável sem infraestrutura;
- é possível provar que regras não publicadas não são chamadas;
- regras Python exigem revisão de código, mas são suficientes para validar contratos;
- ordem, versões e hashes do ruleset ficam explícitos;
- uma futura DSL poderá implementar o mesmo protocolo sem alterar a API do motor.

## Alternativas consideradas

- **DSL própria imediata:** rejeitada por custo e rigidez prematuros.
- **Expressões dinâmicas/eval:** rejeitadas por segurança, auditabilidade e tipagem.
- **Regras dentro dos endpoints:** rejeitadas por violar as fronteiras arquiteturais.
- **Consultar regras “atuais” no banco durante a execução:** rejeitada por não determinismo e baixa reprodutibilidade.
- **Motor baseado em IA:** rejeitado como decisor silencioso; IA futura poderá apenas auxiliar explicação/curadoria com rastreabilidade.

## Critérios de revisão

Revisar após casos de uso fiscais reais formalmente especificados, métricas de complexidade das condições ou necessidade comprovada de gestão declarativa por especialistas.
