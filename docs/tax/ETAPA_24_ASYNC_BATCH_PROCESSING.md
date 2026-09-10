# Etapa 24 — Processamento assíncrono do lote (RNF-08)

- **Data:** 2026-09-10
- **Ator:** Guilherme Nunes, na capacidade de responsável tributário e jurídico do projeto
  (`legal-approver-guilherme-nunes`). Plano formal revisado e aprovado antes da implementação
  (Plan Mode), escolhendo explicitamente esta frente entre as duas recomendadas ao final da
  Etapa 23 (a outra, leitura de XML de NF-e/CT-e, segue exigindo autorização própria).
- **Decisão arquitetural:** [ADR-0028 — Processamento assíncrono do lote (RNF-08)](../adr/0028-processamento-assincrono-de-lote.md).

## 1. O que mudou

A Etapa 23 processava o lote inteiro dentro da própria requisição HTTP — `POST /batch-
classification/{id}/process` bloqueava até a última linha ser avaliada. Esta etapa torna esse
processamento assíncrono, sem introduzir nenhuma infraestrutura nova (nem Redis, nem Celery/RQ,
nem um segundo processo de worker) e sem tocar em nenhum conteúdo tributário:

1. `POST /process`/`POST /reprocess` agora transicionam o lote para `PROCESSING` de forma
   síncrona e devolvem `BatchSummary` **imediatamente** — o processamento de fato roda em
   segundo plano (`fastapi.BackgroundTasks`), numa função (`run_batch_job`) com sua própria
   sessão de banco, chamando linha a linha exatamente o mesmo `process_batch_row` da Etapa 23.
2. Cada linha processada e cada atualização de progresso agora são **committadas
   imediatamente** (antes só eram `flush`), para que uma chamada `GET /{id}` concorrente — o
   polling do frontend — veja o progresso real, não apenas o resultado final.
3. `FAILED` passa a ser realmente alcançável: qualquer exceção não tratada dentro da tarefa em
   segundo plano marca o lote como `FAILED` (com `completed_at` preenchido) em vez de deixá-lo
   preso silenciosamente em `PROCESSING` para sempre.
4. O frontend (`/reforma-tributaria/consulta-lote`) ganhou o primeiro polling deste projeto:
   `GET /{id}` a cada 1 segundo enquanto `status === "PROCESSING"`, com uma barra de progresso
   real (linhas processadas/total) e parada automática ao concluir.
5. **Correção motivada diretamente por esta etapa**: como o polling passou a chamar `GET /{id}`
   repetidamente durante o processamento de até 500 linhas, uma consulta por linha
   (`get_evaluation`, um `SELECT` por linha com resultado) se tornaria custosa sem necessidade.
   Um novo `get_evaluations` (lote, uma única consulta `WHERE id IN (...)`) e `expand_row_results`
   substituem o padrão "um a um" em `GET /{id}` e em `export()`.
6. **Bug real encontrado e corrigido durante a própria implementação**: `mark_processing` (que
   transiciona o lote para `PROCESSING`) só fazia `flush()`, nunca `commit()`. Isso teria duas
   consequências reais: (a) a transição para `PROCESSING` seria **perdida** quando a sessão da
   requisição fosse fechada ao final da resposta (rollback implícito de uma transação nunca
   commitada); e (b) o bloqueio de linha (lock) dessa transação nunca liberada travaria
   indefinidamente a tarefa em segundo plano tentando atualizar a mesma linha (confirmado ao
   vivo: um teste de integração expôs exatamente esse deadlock contra o Postgres real antes da
   correção). Corrigido trocando `flush()` por `commit()` em `mark_processing`.

## 2. Testes executados

- **Unitários** (`test_batch_classification.py`, sem Postgres): 2 novos testes de
  `expand_row_results` — confirma uma única chamada a `get_evaluations` para N linhas (não N
  chamadas), e o caso de lote vazio.
- **Integração real** (`test_batch_classification_integration.py`, Postgres-gated, 9 testes — 6
  reescritos para o novo fluxo em duas etapas + 3 novos):
  - Todos os cenários da Etapa 23 (conclusivo real, sem cobertura, erro isolado, isolamento entre
    organizações, reprodução determinística do reprocessamento, exportação) continuam passando,
    agora chamando explicitamente a rota (`process`/`reprocess`, que só enfileira) e depois
    `run_batch_job` diretamente — o mesmo padrão que a documentação do FastAPI recomenda para
    testar `BackgroundTasks`.
  - **Novo**: `process` retorna imediatamente sem tocar nenhuma linha — confirmado consultando o
    banco logo após a chamada (linha continua `PENDING`) e inspecionando a tarefa enfileirada
    (`background_tasks.tasks[0].func is run_batch_job`) sem executá-la.
  - **Novo**: uma exceção não tratada no meio do laço (`process_batch_row` provocado a lançar via
    `monkeypatch`) resulta em `status=FAILED`, `completed_at` preenchido, sem propagar a exceção
    nem travar o processo.
  - **Novo**: uma escrita tardia num lote já `COMPLETED` é rejeitada pelo trigger real do
    Postgres (`protect_completed_batch`, Etapa 23) — prova que uma tarefa duplicada/atrasada
    nunca corrompe silenciosamente um resultado já concluído.
- **Suíte completa**: `uv run pytest` → **288 passaram, 21 pulados sem `POSTGRES_TESTS=1`**
  (esperado); **309 passaram com `POSTGRES_TESTS=1`**, contra um banco recriado do zero (migração
  0009 aplicada — **nenhuma migração nova nesta etapa**, `FAILED`/`VALIDATED` já existiam desde a
  0010). `ruff check .` e `mypy backend/src tax-engine/src importers/src` limpos.
- **Frontend** (`batch-consultation.test.tsx`, 2 novos testes, 7 no arquivo, 30 no total):
  confirma que uma linha `PENDING` (ainda não alcançada pelo job) nunca aparece rotulada como
  erro (regressão corrigida nesta etapa); confirma via `vi.useFakeTimers()`/
  `advanceTimersByTimeAsync` que o polling mostra progresso real enquanto `PROCESSING` e para de
  chamar `GET /{id}` assim que o lote conclui. `pnpm lint`/`typecheck`/`build` limpos.

## 3. Demonstração ao vivo

Banco de demonstração real, API e frontend locais, login `analyst@example.invalid`, em
`/reforma-tributaria/consulta-lote`, com uma planilha sintética de 41 linhas (40 fora do capítulo
30 da NCM + 1 dentro dele, sem fatos de contexto preenchidos) — deliberadamente **sem** nenhum
`sleep()` adicionado ao código de produção só para alongar a demonstração:

- `POST /process` respondeu imediatamente com `status: "PROCESSING"` (confirmado pelo log da API
  — a resposta chegou antes de qualquer linha ser avaliada).
- A janela de `PROCESSING` foi real, ainda que curta (processamento local de 41 linhas sem I/O
  externo é rápido): o log da API mostra exatamente 2 chamadas a `GET /{id}` — a primeira ainda
  com `PROCESSING` (ativando o polling no frontend), a segunda já com `COMPLETED` (parando-o) —
  confirmado que nenhuma terceira chamada ocorreu nos segundos seguintes.
- Resultado final: 40 linhas `SEM_COBERTURA_NORMATIVA` (NCM fora do capítulo 30) e 1 linha com
  candidato de descoberta encontrado (capítulo 30 → RT-IBSCBS-0004/0005) mas **sem nenhum fato de
  contexto informado nesta planilha** — mapeada corretamente para `SEM_COBERTURA_NORMATIVA`
  também, com a observação explícita "candidato descartado pelos próprios fatos, não ausência de
  descoberta" (a distinção do item 4/decisão do ADR-0028, nunca antes exercitada ao vivo).
- Persistência confirmada por consulta SQL direta ao banco de demonstração:
  `classification_batches.status = COMPLETED`, `processed_count = 41`, `error_count = 0`.
- Exportação confirmada real após a conclusão (200 OK, `.xlsx` válido, ~7 KB).

## 4. Cobertura executável antes/depois

**Inalterada: 4/164 cClassTrib (2,44%).** Esta etapa é puramente de infraestrutura de
processamento — nenhuma regra tributária nova, nenhuma reinterpretação jurídica.

## 5. Pendências

- Um lote `PROCESSING` fica preso se o processo do servidor reiniciar no meio — sem fila
  persistente, não há retomada automática (aceito, ver ADR-0028 item 7 e critério de revisão).
- `BackgroundTasks` roda no mesmo processo/worker da API — não escala além de uma única
  instância; revisar quando houver múltiplas instâncias ou hospedagem compartilhada (ADR-0005).
- Leitura de XML de NF-e/CT-e (e-Auditoria) e cálculo financeiro amplo continuam fora do escopo,
  exigindo autorização própria, como em todas as etapas anteriores.

## 6. Próxima etapa recomendada

Com o lote agora assíncrono e a descoberta funcionando corretamente para ambos os catálogos,
duas frentes seguem abertas, sem ordem obrigatória: avançar a leitura de XML de NF-e/CT-e como
nova fonte de identificação de objeto (reaproveitando esta mesma infraestrutura de lote), ou
revisar a decisão de hospedagem do ADR-0005 agora que há uma primeira carga de processamento em
segundo plano rodando em produção local.

## O que isso NÃO faz

- Não publica nenhuma regra tributária nova nem aprova interpretação jurídica nova.
- Não introduz nenhuma infraestrutura nova (sem Redis, sem Celery/RQ, sem worker separado, sem
  WebSocket/SSE) — usa apenas `fastapi.BackgroundTasks`, já disponível.
- Não resolve escala além de uma única instância da API — aceito e documentado, não escondido.
- Não altera nenhuma das 5 regras reais publicadas, a descoberta fail-closed da Etapa 22, ou o
  contrato de `GET /{id}`/`GET /`/`export` — só `process`/`reprocess` mudam de contrato
  (`BatchDetailResponse` → `BatchSummary`), uma API que nasceu na etapa imediatamente anterior.
- Não introduz nenhuma migração de banco — as tabelas e status (`FAILED`/`VALIDATED`) já existiam
  desde a Etapa 23 (migração 0010); esta etapa apenas passou a usá-los de fato.
