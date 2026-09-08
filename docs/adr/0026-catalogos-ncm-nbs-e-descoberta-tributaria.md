# ADR-0026 — Catálogos NCM/NBS e descoberta tributária assistida

- **Estado:** Aceito
- **Data:** 2026-09-08
- **Relacionados:** ADR-0013, ADR-0014, ADR-0016, ADR-0019, ADR-0025

## Contexto

A plataforma permitia avaliar qualquer combinação das 5 regras reais publicadas (Etapa 21), mas
só se o usuário já soubesse de antemão quais regras pesquisar. `product.ncm`/`FactSet.ncm` eram
strings livres sem nenhum catálogo por trás (`ProductRecord.ncm: String(8)` sem FK,
`RT-IBSCBS-0004` usa `product.ncm_sh` só como fato de string livre). Esta etapa fecha essa
lacuna com catálogos governados de NCM e NBS e uma camada de descoberta que sugere, sem nunca
decidir, quais famílias de regras podem se aplicar a um objeto pesquisado.

Fontes oficiais confirmadas ao vivo (baixadas, inspecionadas e commitadas nesta etapa):
- **NCM**: `https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json`
  (Receita Federal/Siscomex) — JSON, vigência e ato legal por código.
- **NBS**: `https://www.gov.br/mdic/pt-br/images/REPOSITORIO/scs/decos/NBS/NBSa_2-0.csv`
  (MDIC/RFB) — CSV, versão única "NBS 2.0" vigente desde 01/01/2019.
- **Anexo VIII** (correlação oficial NBS↔cIndOp↔cClassTrib, RFB/Portal NFS-e) existe e é real,
  mas nenhum dos 27 cClassTrib que cita corresponde às 4 cClassTrib das 5 regras já publicadas
  (200009/200010/200022/200023 — bens/ZFM/autarquia, não serviços).

## Decisão

1. **Dois catálogos governados paralelos, não uma extensão do catálogo cClassTrib.** NCM e NBS
   ganham cada um seu próprio par identidade/versão (`ncm_catalogs`/`ncm_catalog_versions`,
   `nbs_catalogs`/`nbs_catalog_versions`), replicando exatamente o padrão de
   `TaxClassificationCatalogRecord`/`TaxClassificationCatalogVersionRecord` (ADR-0013):
   proveniência completa (`legal_source_id`, `artifact_hash`/`normalized_hash`,
   `official_url`/`publication_date`/`consulted_at`), ciclo de vida
   `IMPORTED→VALIDATED→IN_REVIEW→APPROVED→PUBLISHED` reaproveitando **sem nenhuma mudança**
   `CatalogStatus`/`TaxonomyService`/`CatalogLifecyclePolicy` (já genéricos via `Protocol`), e
   append-only lifecycle events com trigger de imutabilidade análogo. Não se estende
   `TaxClassificationCatalogVersionRecord` porque seus campos (`cst_count`/`cclasstrib_count`)
   são específicos do cClassTrib.
2. **Hash calculado localmente, como já ocorre para o cClassTrib.** Nem NCM nem NBS publicam
   checksum oficial; `artifact_hash` (bytes crus) e `normalized_hash` (JSON canônico) são
   calculados na implantação e pinados no manifesto, seguindo o padrão já estabelecido.
3. **NCM preserva vigência por código** (`valid_from`/`valid_to`/`legal_act` em `ncm_codes`,
   vindos de `Data_Inicio`/`Data_Fim`/`Tipo_Ato_Ini` da própria fonte); **NBS tem vigência de
   tabela inteira** (a versão "2.0" inteira, sem granularidade por código) — reflete
   exatamente a granularidade real de cada fonte, sem inventar histórico que a fonte não dá.
4. **Camada de descoberta como registro de código fail-closed** (`tax_engine.
   tax_candidate_discovery`), no mesmo espírito de `rule_scope_registry` (ADR-0025) — não um
   workflow de aprovação em banco. Justificativa: a descoberta é orquestração de busca ("que
   famílias de regras revisar"), não conteúdo normativo novo; o conteúdo normativo em si (a
   regra, seu ruleset, sua aprovação) continua exatamente onde já estava.
5. **Semente da descoberta: Capítulo 30 da NCM → RT-IBSCBS-0004/RT-IBSCBS-0005.** Decisão sua,
   confirmada explicitamente: usar o agrupamento oficial da própria tabela NCM ("Produtos
   farmacêuticos", um fato estrutural do governo) combinado com o escopo já declarado nas
   especificações aprovadas dessas duas regras — não é inferência por semelhança de descrição
   nem por IA. **NBS fica intencionalmente vazio nesta etapa**: o Anexo VIII é uma correlação
   oficial real, mas nenhuma das cClassTrib que cita aponta para uma regra hoje publicada
   (correlaciona tributação geral de serviços, não os 4 pilotos de bens/ZFM/autarquia) —
   wireá-lo agora só produziria "candidato identificado, sem regra disponível" para qualquer
   busca, nunca uma avaliação executável. Fica documentado no código e nesta ADR como fonte
   real para uma etapa futura.
6. **Busca é puramente literal e não-ranqueada**, mesmo contrato já usado por
   `/taxonomy/ibs-cbs/csts`/`/classifications` (ADR-0013): `ILIKE` case-insensitive sobre
   código/descrição, apenas na versão `PUBLISHED`. Nunca afirma tratamento tributário — retorna
   o objeto catalogado, não uma classificação fiscal.
7. **Descoberta nunca é um erro, mesmo sem cobertura.** `GET /catalog-discovery/candidates`
   sempre responde 200; `NO_COVERAGE` é uma resposta normal e esperada, não uma falha. Um
   código fora do registro nunca vira `KeyError`/500 nem assume "a hipótese mais comum" — o
   `.get()` do dicionário Python retorna `None`, que vira `NO_COVERAGE` na API.
8. **Integração aditiva com a consulta unificada** (Etapa 21): o frontend usa a sugestão de
   descoberta apenas para pré-marcar checkboxes já existentes (`setSelected`) — o usuário ainda
   confirma e o motor ainda exige os mesmos fatos de sempre. Nenhum contrato/endpoint da Etapa
   21 muda; `GET /catalog-discovery/search` e `GET /catalog-discovery/candidates` são
   inteiramente novos e aditivos.

## Consequências

- Buscar por NCM/NBS/código interno/descrição passa a retornar um objeto real, governado e
  versionado, em vez de depender do usuário digitar um código de memória.
- A descoberta é deliberadamente conservadora: cobre hoje só 1 de 164 cClassTrib de forma
  indireta (via capítulo 30 → 2 regras), e documenta explicitamente onde ainda não há
  cobertura, em vez de fingir uma cobertura mais ampla.
- Adicionar uma 6ª regra real à descoberta exige uma entrada revisada em
  `tax_candidate_discovery.py`, com a mesma seriedade de qualquer outro metadado governado —
  não é automático.
- O Anexo VIII fica registrado como uma fonte real e válida para quando a plataforma publicar
  regras de serviços — não precisa ser repesquisado do zero numa etapa futura.

## Alternativas consideradas

1. **Estender `TaxClassificationCatalogVersionRecord` para NCM/NBS:** rejeitada — os campos de
   contagem são específicos do cClassTrib e forçariam colunas nulas/genéricas sem necessidade.
2. **Persistir a descoberta como tabela governada em banco, com workflow de aprovação:**
   rejeitada por desproporcional ao que é — orquestração de busca, não conteúdo normativo —,
   mesma razão que já levou `rule_scope_registry` a ser um registro em código.
3. **Wireiar o Anexo VIII agora, mesmo sem apontar para nenhuma regra publicada:** rejeitada —
   produziria só "candidato sem regra" em todo caminho de NBS, criando expectativa de cobertura
   que não existe.
4. **Inferir correlação NCM/NBS → cClassTrib por semelhança textual ou modelo de linguagem:**
   rejeitada explicitamente pelo escopo desta etapa — nunca substitui fundamento governado por
   inferência.

## Critérios de revisão

Revisar antes de: adicionar uma nova entrada de descoberta (nova regra ou o Anexo VIII quando
alguma regra de serviços for publicada); promover NCM/NBS a chave obrigatória de cadastro de
produto; ou criar qualquer mapeamento automático NCM/NBS → CST/cClassTrib.
