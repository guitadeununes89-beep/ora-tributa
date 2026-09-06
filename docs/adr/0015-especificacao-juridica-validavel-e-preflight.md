# ADR-0015 — Especificação jurídica validável e pre-flight de implementação

- **Estado:** Aceito
- **Data:** 2026-08-29

## Contexto

A primeira regra tributária brasileira somente poderá ser implementada depois de uma especificação
jurídica formalmente elaborada, revisada e aprovada. Markdown livre é adequado para leitura humana,
mas insuficiente para validar de forma inequívoca campos, datas, referências ao catálogo e casos de
teste. O validador não pode interpretar a legislação nem transformar completude estrutural em
aprovação jurídica.

O catálogo CST IBS/CBS e cClassTrib da Etapa 5 permanece a única fonte de verdade para códigos e
relacionamentos. Não há especificação real aprovada nesta data.

## Decisão

### Artefato canônico

Cada especificação será um documento JSON versionado em `docs/tax/rules/specifications/`. O
template Markdown documenta o preenchimento; o JSON é a fonte canônica validável. Campos
desconhecidos são recusados. Textos jurídicos continuam escritos por pessoas e não são inferidos
pelo sistema.

O documento contém:

- identidade, versão e lifecycle;
- domínio, objetivo, jurisdição e temporalidade;
- fonte oficial referenciada por `legal_source_id`, URL e dispositivo específico;
- `catalog_version_id`, CST e eventual cClassTrib;
- fatos obrigatórios e opcionais, condições, resultado, exclusões e conflitos;
- precedência apenas quando acompanhada de fundamento;
- casos positivos, negativos, insuficientes e de limites de data;
- elaboração, revisão, aprovação e posterior mapeamento para `TaxRuleVersion`;
- marcador `is_synthetic` para fixtures explicitamente fictícias.

### Lifecycle documental

O fluxo permitido é:

`DRAFT → IN_REVIEW → APPROVED → IMPLEMENTED → SUPERSEDED`.

Somente `APPROVED` produz `READY_FOR_IMPLEMENTATION`. `IMPLEMENTED` exige referência a
`tax_rule_identity_id` e `tax_rule_version_id`, mas representa uma especificação já consumida,
não uma nova autorização. `SUPERSEDED` exige referência à especificação substituta.

Transições serão documentadas e revisadas no Git nesta etapa; não haverá editor nem workflow de
mutação via API.

### Pre-flight

Um serviço puro valida schema, coerência de datas, lifecycle, aprovação e casos obrigatórios. Um
adaptador PostgreSQL verifica, na organização autenticada:

1. existência da fonte normativa;
2. existência e status `PUBLISHED` do snapshot exato do catálogo;
3. existência do CST nesse snapshot;
4. existência da cClassTrib, quando informada;
5. compatibilidade estrutural cClassTrib/CST no mesmo snapshot.

O resultado é exclusivamente `READY_FOR_IMPLEMENTATION` ou `NOT_READY`, acompanhado de códigos
e caminhos exatos dos problemas. `READY` significa completude estrutural e referências
resolvidas; não atesta correção da interpretação jurídica.

O comando `validate-tax-rule-spec` usa o mesmo serviço da API. A curadoria oferece somente leitura
do readiness dos arquivos conhecidos, sem edição sofisticada.

### Barreira de proveniência futura

Toda futura `TaxRuleVersion` real deverá preservar
`specification_id`, `specification_version`, `legal_source_id`,
`catalog_version_id` e metadados de aprovação. A etapa posterior deverá criar constraint ou
contrato persistente para esses campos antes de registrar o primeiro adaptador real.

Não haverá geração automática de lógica executável a partir do JSON. A implementação continuará
allowlisted, revisada e testada.

## Consequências

- O formato JSON é mais rígido que Markdown, mas fornece erros determinísticos, diff revisável e
  validação sem nova dependência de parser.
- O filesystem versionado é suficiente para esta etapa preparatória; persistência documental no
  banco poderá ser proposta quando houver workflow colaborativo.
- A curadoria depende de banco migrado para validar fonte e catálogo.
- Uma especificação pode estar estruturalmente válida e juridicamente errada; a aprovação humana
  continua obrigatória e separada.

## Alternativas consideradas

1. **Markdown livre como fonte canônica:** rejeitado por ambiguidade de parsing.
2. **YAML:** adiado para evitar dependência e diferenças de coerção de tipos.
3. **Persistir especificações imediatamente:** adiado; acrescentaria migração e editor antes de
   existir a primeira especificação real.
4. **Gerar regra executável automaticamente:** rejeitado por risco jurídico e quebra do modelo
   allowlisted.
5. **Validar códigos contra uma cópia no documento:** rejeitado; o snapshot publicado é a fonte de
   verdade.

## Critérios de revisão

Revisar antes do primeiro adaptador real, da persistência de especificações, de assinaturas
digitais, de edição web ou de geração assistida por IA.

