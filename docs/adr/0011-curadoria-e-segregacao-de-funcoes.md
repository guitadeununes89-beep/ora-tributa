# ADR-0011 — Curadoria e segregação de funções

- **Status:** Aceita
- **Data:** 2026-08-29
- **Relacionados:** ADR-0006 e ADR-0009

## Contexto

Ainda não haverá autenticação completa, mas a fundação não pode pressupor que criação, aprovação e
publicação sejam atos equivalentes. Os identificadores de ator precisam sobreviver à futura adoção
de identidade e autorização reais.

## Decisão

Os endpoints administrativos exigem `actor_id`, `correlation_id` e justificativa nos comandos de
transição. Esses valores são metadados declarados pelo cliente nesta etapa e **não constituem
autenticação**.

O serviço recebe uma política de segregação configurável. Quando ativada:

- o criador não pode aprovar a própria versão;
- o aprovador não pode publicá-la;
- o publicador de ruleset deve ser diferente dos criadores das versões nele contidas.

A política é uma interface de aplicação substituível; autenticação e papéis futuros poderão
fornecer identidade confiável sem alterar o motor. Toda transição cria, na mesma transação, um
evento específico de lifecycle e um `audit_event` transversal.

Somente `DRAFT` pode ter conteúdo editado. `IN_REVIEW` congela o snapshot submetido. Publicar exige
fonte, dispositivo, jurisdição, vigência, hash, aprovação e atores. `APPROVED` não é executável.

## Alternativas consideradas

- **Adiar qualquer noção de ator:** rejeitado porque criaria eventos sem responsabilização.
- **Implementar autenticação agora:** rejeitado por ampliar o escopo antes do ADR de segurança e
  tenancy.
- **Política fixa no endpoint:** rejeitada por acoplar governança ao transporte HTTP.
- **Permitir edição durante revisão:** rejeitada porque o aprovado poderia diferir do revisado.

## Consequências

Os endpoints são adequados apenas para desenvolvimento controlado e devem ser desabilitados ou
protegidos antes de produção. Testes podem ativar a segregação independentemente de autenticação.

## Critérios de revisão

Substituir os atores declarados quando identidade, papéis, tenant e assinatura forem definidos.

