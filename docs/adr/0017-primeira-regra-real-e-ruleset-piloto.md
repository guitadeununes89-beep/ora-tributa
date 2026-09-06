# ADR-0017 — Primeira regra tributária real e ruleset piloto explícito

- **Estado:** Aceito
- **Data:** 2026-08-31
- **Relacionados:** ADR-0006, ADR-0009, ADR-0010, ADR-0011, ADR-0012 e ADR-0015

## Contexto

A RT-IBSCBS-0003 é a primeira especificação jurídica candidata à implementação real. O modelo
atual aceita apenas identidades sintéticas, resolve somente implementações sintéticas e não possui
campos persistentes específicos para ligar uma `TaxRuleVersion` à especificação aprovada e ao
snapshot do catálogo. Permitir a primeira regra real sem essas barreiras quebraria a proveniência.

O responsável tributário e jurídico do projeto declarou revisão e aprovação integral da
RT-IBSCBS-0003 v2. A mesma pessoa acumulará excepcionalmente revisão e aprovação documental. Essa
exceção não elimina a segregação operacional: criação técnica da versão, aprovação da versão,
publicação da versão e publicação do ruleset continuam atribuídas a atores governados compatíveis.

## Decisão

1. A RT-IBSCBS-0003 v2 será a única especificação real implementada nesta etapa.
2. A aprovação documental usará um ator humano governado identificado por ID estável e capacidade,
   sem armazenar documento pessoal em fonte, logs ou metadados de auditoria.
3. O acúmulo de `reviewed_by` e `approved_by` pela mesma pessoa é aceito somente para este piloto e
   ficará explícito na evidência de aprovação. O Codex não será revisor ou aprovador jurídico.
4. A restrição física que força toda identidade a ser sintética será removida por migração. Regras
   reais exigirão, no serviço, especificação `APPROVED`, hash exato, fonte oficial, catálogo
   `PUBLISHED`, CST/cClassTrib existentes e metadados de aprovação.
5. `TaxRuleVersion` ganhará proveniência persistente: specification ID/version/hash,
   `catalog_version_id`, CST, cClassTrib e approval metadata. Fixtures antigas podem manter esses
   campos nulos; versões reais não.
6. A implementação será Python allowlisted por chave estável. Não haverá `eval`, código no banco,
   geração automática a partir do JSON ou acesso do `tax-engine` ao PostgreSQL/API.
7. A regra representará exclusivamente o art. 146, § 1º, I. A descrição compartilhada da
   cClassTrib 200010 não autoriza incorporar o inciso II.
8. O ruleset `IBSCBS-PILOT-001` conterá exclusivamente a RT-IBSCBS-0003 v1, será publicado de forma
   imutável e só será usado quando solicitado explicitamente. Não será padrão de produção.
9. A API aceitará os fatos reais estritamente definidos para este piloto. CNPJ, nome ou descrição
   não inferem natureza jurídica.
10. Toda avaliação real registrará evento de auditoria e preservará ruleset, fingerprint, versão da
    regra, catálogo, entrada e DecisionTrace.

## Consequências

- a primeira regra real fica reproduzível e separada das fixtures sintéticas;
- outras especificações DRAFT continuam inelegíveis e sem implementação;
- a aplicação passa a manter um registro allowlisted de implementações reais;
- correção após publicação exige RT-IBSCBS-0003 v2 e novo ruleset;
- a exceção de mesma pessoa para revisão/aprovação documental não deve ser generalizada sem nova
  decisão de governança.

## Alternativas consideradas

1. **Usar os usuários fictícios como aprovadores jurídicos:** rejeitada por falsa atribuição.
2. **Persistir toda a proveniência apenas em JSON:** rejeitada por não expressar referências e
   invariantes essenciais no schema.
3. **Reutilizar o resolver sintético:** rejeitada porque misturaria regra real e fixture.
4. **Ativar o piloto como ruleset padrão:** rejeitada pelo escopo restrito e risco operacional.
5. **Inferir natureza jurídica por CNPJ ou nome:** rejeitada por insuficiência jurídica e técnica.

## Critérios de revisão

Revisar antes da segunda regra real, de produção, de aprovação com assinatura externa, da retirada
da exceção documental ou de qualquer integração automática de Receita Federal/Anvisa.
