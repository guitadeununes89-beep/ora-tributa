# ADR-0014 — Produto e enquadramento assistido IBS/CBS

- **Estado:** Aceito
- **Data:** 2026-08-29

## Contexto

A plataforma precisa associar fatos de produto e operação a regras determinísticas publicadas,
produzindo candidatos CST/cClassTrib sem transformar NCM, GTIN, CEST ou descrição em decisão
isolada. Não há, nesta data, especificação jurídica real marcada `APPROVED` para execução em
`docs/tax/rules/`. A infraestrutura deve funcionar e ser testável com fixtures sintéticas, mas
permanecer fail-closed para regras reais.

Produtos mudam ao longo do tempo. Uma avaliação histórica deve usar o snapshot do produto, dos
atributos, do ruleset e do catálogo conhecidos na avaliação original. O catálogo normativo da
Etapa 5 é a única autoridade para códigos CST/cClassTrib.

## Decisão

### Produto e temporalidade

- `Product` é tenant-scoped e contém apenas identidade e dados cadastrais comuns: código interno e
  descrição obrigatórios; GTIN, NCM e CEST opcionais; unidade obrigatória; status explícito.
- Cada criação ou alteração gera um `ProductVersion` imutável com intervalo de tempo de registro
  (`recorded_at`/`superseded_at`) e snapshot completo dos campos tributariamente relevantes.
- Atributos fiscais ficam em `ProductTaxAttributeVersion`, identificados por chave técnica e
  versionados separadamente. Nesta etapa somente chaves sintéticas `synthetic.*` podem ser
  exercitadas; atributos jurídicos reais exigem especificação aprovada.
- `ProductTaxReview` registra que uma avaliação histórica pode precisar de nova análise. Ele não
  altera nem invalida a avaliação anterior.

### FactSet

O motor puro admite: `product_id`, `product_version_id`, código, descrição, NCM, NBS, tipo de
operação, UF de origem/destino, tipo de destinatário, regime e mapa imutável de atributos. Cada
campo tem significado literal; presença não implica relevância jurídica. O FactSet arquivado é o
snapshot efetivamente avaliado e participa do hash de entrada.

### Regras e catálogo

- Uma regra executável continua sendo uma versão publicada em ruleset publicado e vigente na data
  da operação.
- Regra real exige documento conforme `docs/tax/RULE_SPECIFICATION_TEMPLATE.md` com status
  `APPROVED`, revisão identificada e fonte oficial. A ausência desse documento impede o adaptador
  executável de ser registrado.
- Candidato é estruturado por `catalog_version_id`, `CST`, eventual `cClassTrib`, versão da regra,
  condições e suporte determinístico. Antes da avaliação, o backend valida que catálogo e códigos
  referenciados existem no mesmo snapshot `PUBLISHED`.
- O motor não copia descrições normativas nem consulta PostgreSQL. O backend enriquece a resposta
  com a descrição do catálogo após validar a referência.

### Candidatos, ausência e conflitos

- Suporte permitido: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_FACTS`; não representa
  probabilidade.
- Uma regra com fatos ausentes retorna `INSUFFICIENT_FACTS` e caminhos canônicos como
  `product.attributes.<chave>`; não pode produzir conclusão.
- Um candidato integralmente suportado gera `CONCLUSIVO` somente se for o único resultado distinto.
- Dois ou mais candidatos distintos, sem precedência aprovada, geram
  `POSSIVEIS_ENQUADRAMENTOS`. Não há desempate por ordem, especificidade presumida ou NCM.
- Fatos ausentes relevantes têm precedência sobre conclusão e geram `NECESSITA_VALIDACAO`.
- Nenhuma regra aplicável gera `SEM_CLASSIFICACAO`.
- Regras mutuamente exclusivas, complementares e precedência só podem ser declaradas na
  especificação jurídica aprovada. Não será criada DSL genérica nesta etapa.

### DecisionTrace e auditoria

Seleção, avaliação, validação de catálogo e agregação geram passos ordenados. A avaliação arquiva
versões exatas de produto, ruleset, regras, catálogo, fatos e hash. A API registra
`TAX_CLASSIFICATION_REQUESTED` e `TAX_CLASSIFICATION_COMPLETED`; revisão humana futura registra
`TAX_CLASSIFICATION_REVIEWED`.

Eventos cadastrais são `PRODUCT_CREATED`, `PRODUCT_UPDATED` e
`PRODUCT_TAX_ATTRIBUTE_CHANGED`, sempre com ator e organização autenticados.

### API e autorização

- CRUD de produto é tenant-scoped; leitura requer `READ` e mutação usa `MANAGE_COMPANY` nesta
  etapa, pois ainda não existe permissão específica de catálogo de produtos.
- Classificação usa `RUN_EVALUATION` e nunca aceita `organization_id` do cliente.
- `POST /api/v1/tax/ibs-cbs/classify` aceita `product_id` ou fatos manuais. Se houver produto, o
  backend monta o FactSet do snapshot atual; fatos manuais explícitos podem complementar, nunca
  reescrever silenciosamente o histórico.

## Consequências

- Há mais armazenamento por snapshot, em troca de reprodução histórica e auditoria confiáveis.
- A interface pode coletar fatos ausentes sem fingir conclusão.
- O fluxo real permanecerá em `SEM_CLASSIFICACAO` enquanto não houver regra jurídica aprovada e
  ruleset publicado compatível. Cenários conclusivos e conflitantes são demonstrados apenas em
  testes sintéticos.
- Uma permissão `MANAGE_PRODUCT` e temporalidade jurídica dos atributos poderão ser propostas em
  ADR futuro.

## Alternativas consideradas

1. **Guardar somente o estado atual do produto:** rejeitada por destruir reprodução histórica.
2. **Armazenar cClassTrib no produto:** rejeitada por transformar avaliação temporal em verdade
   eterna.
3. **NCM como chave de decisão:** rejeitada por insuficiência jurídica e violação das regras do
   projeto.
4. **DSL de precedência genérica:** adiada; sem regras aprovadas não há evidência de necessidade.
5. **IA escolhendo entre candidatos:** rejeitada; IA poderá explicar, nunca desempatar
   silenciosamente.

## Critérios de revisão

Revisar antes de regras reais, atributos fiscais reais, precedência, automação de reavaliação,
importação em massa, IA na coleta de fatos ou nova permissão de produto.
