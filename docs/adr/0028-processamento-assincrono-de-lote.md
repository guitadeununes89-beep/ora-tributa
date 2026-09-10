# ADR-0028 — Processamento assíncrono do lote (RNF-08)

- **Estado:** Aceito
- **Data:** 2026-09-09
- **Relacionados:** ADR-0005, ADR-0027

## Contexto

A Etapa 23 entregou a consulta em lote (`POST /batch-classification/{id}/process`) de forma
síncrona: a requisição HTTP bloqueia até que todas as linhas (até `BATCH_MAX_ROWS`) sejam
avaliadas, e só então devolve o resultado completo. Isso já estava documentado como limitação
conhecida, apontando para o RNF-08 ("processamento em lote futuro assíncrono, idempotente e
reprocessável"), reconhecido desde a fundação do produto (`SPEC_PLATAFORMA_TRIBUTARIA.md`).

Nem infraestrutura de fila/broker (Redis, RabbitMQ) nem biblioteca de tarefas em background
(Celery, RQ, arq, dramatiq, huey) existem hoje neste projeto — `docker-compose.yml` só define
`postgres`, e nenhum `pyproject.toml` do workspace lista uma dessas dependências. Também não há
hoje nenhum polling no frontend. Este ADR decide como tornar o processamento assíncrono sem violar
o espírito do ADR-0005 ("hospedagem agnóstica... infraestrutura de produção será definida depois
de requisitos de segurança, residência de dados, disponibilidade e custo... rejeita complexidade
sem necessidade validada").

## Decisão

1. **`fastapi.BackgroundTasks`, sem nova dependência e sem novo serviço de infraestrutura.**
   `POST /process`/`POST /reprocess` transicionam o lote para `PROCESSING` de forma síncrona
   (o cliente já recebe o estado real na resposta), enfileiram o processamento de fato via
   `background_tasks.add_task(...)` e retornam imediatamente `BatchSummary` — não mais
   `BatchDetailResponse`. É uma mudança deliberada de contrato de uma API que nasceu na própria
   Etapa 23, sem consumidor externo além do frontend do próprio projeto, atualizado na mesma
   etapa.
2. **A tarefa em background tem sua própria sessão de banco** (`get_session_factory()()`,
   `infrastructure/database/session.py`, já existente) — nunca a sessão da requisição HTTP, que já
   estará fechada quando a tarefa executar. Vive como uma função testável e não decorada
   (`run_batch_job`) dentro de `api/routes/batch_classification.py`: monta seus próprios
   repositórios, mas chama `application.batch_classification.process_batch_row` linha a linha
   exatamente como a Etapa 23 já fazia — nenhuma lógica de domínio nova.
3. **Cada linha processada é committada imediatamente** (`update_row_result` passa a `commit()`,
   não só `flush()`), e o cabeçalho do lote recebe um `update_progress(processed_count,
   error_count)` committado a cada linha. É o que permite que um `GET /{id}` concorrente (outra
   sessão/requisição — o polling do frontend) veja o progresso real, não apenas o resultado final.
   Nenhuma migração é necessária: `PROCESSING` já não é bloqueado pelo trigger de imutabilidade
   `protect_completed_batch()` (Etapa 23) — só `COMPLETED`/`FAILED` são, propositalmente.
4. **`FAILED` passa a ser de fato usado.** Esse status já existia no `CHECK` da migração 0010, mas
   nunca era acionado. Qualquer exceção não tratada dentro da tarefa em background agora leva o
   lote a `FAILED` com `completed_at` preenchido (e a exceção registrada via `logging`), em vez de
   deixá-lo preso silenciosamente em `PROCESSING` para sempre.
5. **Polling simples no frontend — sem WebSocket/SSE.** `useEffect` com `setInterval` (1000 ms)
   chamando `GET /batch-classification/{id}` enquanto `status === "PROCESSING"`, parado no
   `unmount` e ao concluir. Primeiro caso de polling no frontend deste projeto; decisão explícita
   de não introduzir um protocolo novo para um progresso já perfeitamente servido por um `GET`
   existente.
6. **Correção motivada diretamente por esta etapa**: `expand_row_result` (Etapa 23) consulta uma
   `Evaluation` por linha com `evaluation_id`, aceitável para uma chamada isolada — mas o polling a
   cada 1s durante o processamento de até 500 linhas multiplicaria isso sem necessidade. Adiciona-se
   `SqlAlchemyGovernanceRepository.get_evaluations(evaluation_ids)` (uma única consulta `WHERE id
   IN (...)`) e `expand_row_results` (lote), usadas por `GET /{id}` e por `export()`. A função
   original `expand_row_result` (uma linha) permanece intocada.
7. **Limitação aceita, não resolvida agora**: um lote `PROCESSING` fica preso se o processo do
   servidor reiniciar no meio — sem fila persistente, não há retomada automática. Aceitável para o
   escopo atual de execução local, single-instance (ADR-0005); revisitar quando houver múltiplas
   instâncias ou hospedagem compartilhada.

## Consequências

- Um lote de 500 linhas deixa de bloquear a conexão HTTP do analista por sua duração inteira; a
  interface pode mostrar progresso real em vez de uma espera indeterminada.
- O processamento continua determinístico e reprocessável (RNF-08): `POST /reprocess` cria um novo
  lote a partir das mesmas linhas cruas e passa pelo mesmo caminho assíncrono.
- Adiciona um estado de falha real (`FAILED`) que nunca existia de fato — lotes travados por bug
  ou indisponibilidade momentânea do catálogo agora terminam visíveis como falha, não como
  silêncio eterno em `PROCESSING`.
- **Não** resolve escala além de uma única instância do processo da API — isso é adiado
  deliberadamente, não esquecido.

## Alternativas consideradas

1. **Celery/RQ com Redis como broker:** rejeitada — introduziria um serviço de infraestrutura novo
   (`docker-compose.yml` ganharia Redis) exatamente no momento em que ADR-0005 registrou que essa
   decisão "será definida depois de requisitos de segurança, residência de dados, disponibilidade
   e custo" — nenhum desses requisitos foi levantado ainda.
2. **Worker de longa duração como processo separado** (um script Python rodando em loop,
   consultando lotes `RECEIVED`): mais robusto a reinícios do servidor web, mas exige operar e
   monitorar um segundo processo continuamente — complexidade operacional desproporcional ao
   volume atual (lotes disparados manualmente por um analista, não um fluxo contínuo).
3. **WebSocket ou Server-Sent Events para progresso via push:** rejeitada — um protocolo novo só
   para evitar polling de um endpoint `GET` que já existe e já é barato o bastante nesta escala.

## Critérios de revisão

Revisar antes de: adotar múltiplas instâncias da API ou hospedagem compartilhada (a limitação do
item 7 deixa de ser aceitável); lotes tipicamente maiores ou mais frequentes o suficiente para o
`BackgroundTasks` in-process (compartilhando o mesmo processo/worker da API) deixar de ser
suficiente; ou se a decisão de hospedagem do ADR-0005 for finalmente tomada.
