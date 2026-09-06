# ADR-0009 — Modelo físico bitemporal e auditoria

- **Status:** Aceita
- **Data:** 2026-08-29
- **Relacionados:** ADR-0002, ADR-0004, ADR-0006 e ADR-0007

## Contexto

A terceira etapa precisa persistir fontes fictícias, identidades lógicas, snapshots de regras,
workflow, rulesets e avaliações reproduzíveis. O banco deve proteger o histórico mesmo quando
uma chamada contornar a API. Ao mesmo tempo, o motor tributário não pode conhecer SQLAlchemy,
PostgreSQL ou modelos ORM.

## Decisão

Usar PostgreSQL 17, SQLAlchemy 2 síncrono e Alembic. Migrações Alembic são a única forma
admitida de alterar o schema. Os modelos e adaptadores ficam em `backend`; o `tax-engine`
continua recebendo somente objetos de domínio resolvidos.

### Tabelas e responsabilidades

- `legal_sources`: fonte normativa separada. Nesta etapa aceita somente fontes marcadas como
  sintéticas; URL, hash e jurisdição são preservados.
- `tax_rule_identities`: identidade lógica estável, independente das versões.
- `tax_rule_versions`: conteúdo e metadados de uma versão. `(rule_identity_id, version)` é
  único. `valid_from` é inclusivo e `valid_to` exclusivo.
- `rule_lifecycle_events`: fonte histórica append-only das transições.
- `rulesets` e `ruleset_items`: cabeçalho e composição exata do snapshot.
- `evaluations` e `evaluation_rule_versions`: envelope, entrada canônica, resultado,
  `DecisionTrace` e versões efetivamente usadas.
- `audit_events`: trilha de negócio transversal append-only, sem PII ou documentos fiscais.

`tax_rule_versions.lifecycle_status` e timestamps como `approved_at` e `published_at` são
projeções mantidas na mesma transação que inclui o evento. A sequência de eventos permanece a
fonte histórica. A projeção existe para constraints, locks e consultas operacionais, e deve ser
reconstruível.

### Imutabilidade e constraints

- conteúdo, fonte, dispositivo, jurisdição, vigência e hash não podem ser alterados depois de
  `DRAFT`;
- versões publicadas não podem ser excluídas e nunca sofrem alteração destrutiva;
- eventos de lifecycle e auditoria não admitem `UPDATE` ou `DELETE`;
- rulesets publicados e seus itens são imutáveis;
- checks validam intervalos, hashes SHA-256, timestamps mínimos de cada estado e referências;
- triggers PostgreSQL reforçam invariantes que envolvem estado anterior ou outra tabela.

Não será usado range de sistema nativo nesta primeira migração. O tempo jurídico usa datas e o
tempo do sistema usa `timestamptz` mais eventos. Essa forma é explícita, portável dentro do
PostgreSQL e corresponde aos contratos atuais.

### Avaliações e reprodução

A entrada normalizada, o resultado e a trilha são armazenados como JSONB, acompanhados de hashes,
versão do motor, fingerprint do ruleset, `operation_date`, `known_at` e versões usadas. Reprodução
carrega o mesmo ruleset imutável e os mesmos fatos; um novo envelope registra quando a reprodução
ocorreu e aponta para a avaliação original.

## Alternativas consideradas

- **SQL puro sem toolkit:** mantém controle total, mas aumenta repetição nos adaptadores e reduz
  checagem estrutural; rejeitado para a fundação.
- **ORM dentro do motor:** rejeitado por violar a fronteira do domínio.
- **Event sourcing integral:** preservaria todo estado, mas elevaria muito a complexidade. Foram
  escolhidos snapshots imutáveis, eventos de lifecycle e projeções transacionais.
- **PostgreSQL temporal/ranges para todas as dimensões:** útil em consultas avançadas, porém
  prematuro; datas e eventos cobrem os critérios atuais.
- **Guardar somente hashes da avaliação:** insuficiente para reprodução e auditoria.
- **Guardar documentos fiscais completos:** fora do escopo e incompatível com minimização de dados.

## Consequências

O schema possui redundância controlada entre eventos e projeções. Toda operação de workflow deve
usar transação e lock pessimista da versão. Triggers tornam falhas explícitas, mas exigem testes
PostgreSQL reais além de testes unitários dos serviços.

## Critérios de revisão

Revisar antes de introduzir tenant, assinatura digital, fontes reais, particionamento de avaliações
ou correções retroativas que exijam ranges de tempo do sistema mais sofisticados.

