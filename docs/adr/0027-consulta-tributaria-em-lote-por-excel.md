# ADR-0027 — Consulta tributária em lote por Excel

- **Estado:** Aceito
- **Data:** 2026-09-09
- **Relacionados:** ADR-0013, ADR-0017, ADR-0019, ADR-0020, ADR-0025, ADR-0026

## Contexto

As Etapas 21 e 22 tornaram a consulta unificada (`POST /tax/ibs-cbs/classify-unified`) e a
descoberta por NCM/NBS (`/catalog-discovery/*`) utilizáveis linha a linha, mas só uma consulta por
vez. A visão de longo prazo (e-Auditoria) e o próprio `SPEC_PLATAFORMA_TRIBUTARIA.md` (seção 6,
RNF-08) já reconheciam "consultas individual e em lote... Excel" como requisito futuro, sem
autorizar implementação. Esta etapa entrega a primeira consulta em lote real, processando cada
linha de uma planilha através da mesma consulta unificada e da mesma descoberta já existentes —
sem motor novo, sem ampliar cobertura jurídica, sem cálculo financeiro, sem XML/EFD.

## Decisão

1. **Reuso literal do motor.** Cada linha do lote chama `EvaluationService.evaluate_many()`
   (o mesmo método usado por `classify_unified`), com o mesmo `FactSet`/`EvaluationContext` e a
   mesma persistência real de `EvaluationRecord`. Uma linha processada gera uma avaliação real,
   auditável e reproduzível — não uma simulação paralela.
2. **Descoberta por linha via a mesma função pura da Etapa 22** (`tax_engine.
   tax_candidate_discovery.discover_by_ncm`/`discover_by_nbs`). A pequena lógica de seleção
   NCM-vs-NBS hoje embutida em `api/routes/catalog_discovery.py` é extraída para uma função de
   aplicação compartilhada, reaproveitada pela rota HTTP existente (sem mudar seu contrato) e pelo
   novo processador de lote — evita duas implementações divergentes da mesma decisão.
3. **Resolução `rule_code → ruleset_id` via `GovernanceRepository.list_rule_versions()`**, já
   usado por `GET /taxonomy/ibs-cbs/coverage` (Etapa 14), em vez de um mapeamento hardcoded. Uma
   regra candidata sem ruleset consultável (`queryable_rulesets`) nunca é inventada — a linha
   recebe `NECESSITA_VALIDACAO` com observação explícita.
4. **Quatro status de classificação, mapeados sem interpretação a partir do `ClassificationStatus`
   real do `tax-engine`**: `CONCLUSIVE`→`CONCLUSIVO`, `POSSIBLE_MATCHES`→`POSSIVEIS_ENQUADRAMENTOS`,
   `REQUIRES_VALIDATION`→`NECESSITA_VALIDACAO`. O quarto, `SEM_COBERTURA_NORMATIVA`, cobre dois
   casos distintos, sempre diferenciados no campo `observations` de cada linha: (a) a descoberta
   não encontrou nenhuma família de regra candidata para o NCM/NBS (`NO_COVERAGE` da Etapa 22); e
   (b) o motor retornou `UNCLASSIFIED` — todas as regras candidatas foram contraditas pelos fatos
   informados, sem nenhum fato faltante (`multi_rule_evaluation.py`, agregação de status). Em
   nenhum dos dois casos a ausência de conclusão é apresentada como tributação geral.
5. **Um status de processamento separado (`PENDING`/`PROCESSED`/`ERROR`)**, distinto dos quatro
   status de classificação acima, cobre falha de identificação da linha: NCM/NBS em formato
   inválido ou inexistente no catálogo `PUBLISHED`, nenhuma coluna de identificação preenchida, ou
   data de operação ilegível. Essas linhas viram `ERROR` com `error_message` e `classification_
   status` nulo — nunca um `SEM_COBERTURA_NORMATIVA` (que pressupõe um objeto identificado sem
   regra, não um objeto não identificável). Uma linha inválida nunca interrompe o lote.
6. **`object_kind` (`GOOD`/`SERVICE`/`OTHER`) é um rótulo de roteamento de busca, não uma
   implementação do `TaxObject` do ADR-0019.** O ADR-0019 reserva esse vocabulário para uma futura
   camada de objeto tributário de primeira classe, com migração e contrato próprios (ADR-0020,
   critério de revisão: "quando um objeto diferente de bem for habilitado"). Esta etapa **não**
   cria `TaxObject`, não migra `Product`/`FactSet`, não altera o tax-engine — usa `object_kind`
   apenas como coluna informativa da linha de lote, que decide qual catálogo pesquisar por
   descrição quando a planilha não informa NCM/NBS diretamente (`GOOD`→NCM, `SERVICE`→NBS,
   ausência/`OTHER`→ambos). Não aciona os critérios de revisão do ADR-0019/0020 porque não
   habilita nenhum comportamento tributário novo para serviço/direito — apenas escolhe onde ler.
7. **Processamento síncrono, dentro da própria requisição HTTP**, não assíncrono/enfileirado. Até
   `BATCH_MAX_ROWS` (padrão 500) avaliações determinísticas puras, sem I/O externo, respondem em
   segundos. O requisito RNF-08 ("processamento em lote futuro assíncrono, idempotente e
   reprocessável") permanece reconhecido como evolução futura, não implementado agora — evita
   introduzir fila/worker sem necessidade real desta etapa.
8. **O arquivo original não é armazenado em disco nem no banco.** Diferente dos artefatos NCM/NBS
   (dados públicos oficiais, propositalmente commitados ao repositório), a planilha de lote é dado
   privado do usuário/organização. Só o hash SHA-256 do arquivo é retido para auditoria; o
   conteúdo é parseado em memória e cada linha crua (`raw_values`) fica persistida como JSON na
   tabela de linhas do lote — suficiente para reprocessar e exportar, sem reter o binário original
   nem exigir política de retenção de arquivo.
9. **Validação de upload conforme `AGENTS.md` §8**: tamanho máximo configurável
   (`BATCH_MAX_FILE_SIZE_BYTES`, padrão 5 MB), extensões aceitas restritas a `.xlsx`/`.csv`,
   verificação de assinatura binária real (magic bytes, não apenas a extensão), rejeição explícita
   de `.xlsm`/`.xlsb`/`.xls` e de qualquer `.xlsx` que contenha `xl/vbaProject.bin` (macro) dentro
   do contêiner zip, e `openpyxl.load_workbook(..., read_only=True, data_only=True,
   keep_links=False)` — o mesmo padrão já aceito em `importers/src/tributaria_importers/
   ibs_cbs_catalog.py` para mitigar XXE e links externos. Fórmulas nunca são avaliadas (sempre
   `data_only=True`). Na exportação, texto do usuário que comece com `=`, `+`, `-` ou `@` é
   neutralizado (prefixo de aspas simples) contra injeção de fórmula no arquivo gerado.
10. **Limite de linhas configurável e explicitamente não definitivo.** Linhas além de
    `BATCH_MAX_ROWS` são reportadas como truncadas na resposta do upload, nunca processadas
    silenciosamente pela metade.
11. **Um lote `COMPLETED`/`FAILED` é imutável** (trigger `protect_completed_batch()`, mesmo molde
    de `protect_published_{prefix}_catalog` da Etapa 22) — reprocessar cria um novo lote a partir
    das mesmas linhas cruas, nunca reescreve o anterior. Isso prova reprodutibilidade sem abrir
    uma exceção ao princípio de imutabilidade pós-conclusão já usado em todo o sistema.

## Consequências

- A consulta em lote não é um segundo motor: qualquer correção/evolução da consulta unificada ou
  da descoberta se propaga automaticamente ao lote, sem manutenção duplicada.
- A cobertura executável **não muda** (permanece 4/164 cClassTrib) — o lote é uma forma de acessar
  a cobertura já existente em volume, não uma nova regra.
- O primeiro upload de arquivo do frontend introduz uma exigência nova de segurança (validação de
  tipo real, não só extensão) que se torna o padrão a seguir por qualquer upload futuro.
- Processamento síncrono limita o tamanho prático do lote ao que responde dentro de um timeout de
  requisição razoável; crescer além disso exige a evolução assíncrona já reconhecida em RNF-08,
  fora do escopo desta etapa.

## Alternativas consideradas

1. **Motor de avaliação dedicado ao lote:** rejeitada — duplicaria `EvaluationService`/
   `MultiRuleEngine` e divergiria da consulta unificada ao primeiro ajuste futuro.
2. **Implementar `TaxObject` (ADR-0019) nesta etapa para dar suporte a "tipo de objeto":**
   rejeitada — ADR-0019/0020 exigem migração e contrato próprios para essa evolução, fora do
   escopo autorizado agora; `object_kind` como rótulo de roteamento de busca resolve a necessidade
   real do lote sem essa migração.
3. **Processamento assíncrono com fila desde já:** rejeitada — nenhuma necessidade real hoje
   (volume ≤ `BATCH_MAX_ROWS`, sem I/O externo); adicionar infraestrutura de fila sem caso de uso
   comprovado contrariaria a prática do projeto de não construir antecipadamente.
4. **Persistir o arquivo original (mesmo padrão dos artefatos NCM/NBS):** rejeitada — artefatos
   governamentais são dados públicos com proveniência a preservar; uma planilha de lote é dado
   privado do cliente, sem motivo para reter o binário além do necessário para reprocessar (que já
   é coberto por `raw_values`).

## Critérios de revisão

Revisar antes de: tornar o processamento assíncrono (RNF-08); habilitar `object_kind` para
determinar tratamento tributário (e não apenas roteamento de busca); elevar `BATCH_MAX_ROWS` a um
valor que exija paginação ou processamento fora da requisição; ou introduzir qualquer persistência
do arquivo original.
