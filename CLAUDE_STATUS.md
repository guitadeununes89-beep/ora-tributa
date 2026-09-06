# Ora Tributa — status de continuidade (Claude Code)

> Este arquivo é gerado/atualizado ao final de cada etapa de trabalho para que o responsável
> humano (Guilherme) possa revisar o que foi feito e orientar a próxima etapa. Ele complementa,
> mas não substitui, `CLAUDE_HANDOFF.md`, `README.md` e `AGENTS.md`.

## Etapa 0 — recepção do pacote e verificação do estado herdado

**Data:** 2026-09-06
**Origem:** pacote `ora-tributa-claude-handoff-20260903-214049.zip`, gerado em 2026-09-03 a partir
de um projeto iniciado no ChatGPT.
**Novo local do projeto:** `C:\Users\gtnunes\ora-tributa` (pasta própria, fora de
`Portal - ApuraSol`, pois é um produto separado).

### O que foi feito nesta etapa

1. Extraído e revisado o pacote: `AGENTS.md`, `CLAUDE_HANDOFF.md`, `README.md`,
   `SPEC_PLATAFORMA_TRIBUTARIA.md` e `PACKAGE_CONTENTS.txt`.
2. Copiado o projeto para `C:\Users\gtnunes\ora-tributa` e inicializado um repositório Git local
   (commit inicial `f3008d6`). **Nenhum remoto foi configurado** — o repositório existe apenas
   localmente até você decidir onde hospedá-lo (GitHub etc.).
3. Preparado o ambiente de desenvolvimento na máquina:
   - Instalado **Python 3.12.10** via winget (o projeto exige 3.12/3.13; a máquina só tinha 3.14,
     que o próprio README marca como incompatível). Python 3.14 permanece instalado, sem conflito.
   - Instalado **uv 0.12.10** via winget.
   - Instalado **pnpm** (via `npx pnpm@11.19.0`, respeitando o `packageManager` fixado no
     `frontend/package.json`; a tentativa inicial com `pnpm` global mais recente falhou por um bug
     de instalação do próprio pacote `pnpm` do npm).
   - **Docker Desktop**: instalação iniciada via winget, mas **parada aguardando você aprovar o
     prompt de UAC (elevação de administrador)** que deve ter aparecido na sua tela. Assim que for
     aprovado, a instalação conclui sozinha; o PostgreSQL só pode ser iniciado depois disso
     (`docker compose up -d postgres`).
4. Executada a validação completa descrita no `CLAUDE_HANDOFF.md`, **sem tocar em nenhuma regra
   fiscal, alíquota ou classificação** (fora do escopo desta etapa):

   | Verificação | Resultado | Esperado no handoff |
   |---|---|---|
   | `uv run ruff check .` | ✅ sem problemas | — |
   | `uv run mypy backend/src tax-engine/src importers/src` | ✅ sem problemas em 76 arquivos | — |
   | `uv run pytest` | ✅ 119 passaram, 1 pulado (`test_postgresql_invariants`, exige Postgres) | 119 passaram, 1 pulado |
   | `pnpm lint` (frontend) | ✅ sem problemas | — |
   | `pnpm typecheck` (frontend) | ✅ sem problemas | — |
   | `pnpm test` (frontend) | ✅ 9 testes passaram em 6 arquivos | 9 testes passaram |

   **O estado herdado bate exatamente com o que o `CLAUDE_HANDOFF.md` descrevia.** Nenhuma
   divergência encontrada entre o pacote recebido e o comportamento real do código.

5. **Não foi possível validar `test_postgresql_invariants` nem subir a API/frontend de ponta a
   ponta** porque o PostgreSQL depende do Docker, que ainda está pendente de aprovação (item 3).

### O que NÃO foi feito (intencionalmente)

- Nenhuma regra tributária, alíquota, cClassTrib, CST ou interpretação jurídica foi criada,
  alterada ou "corrigida" — inclusive a divergência conhecida da `RT-IBSCBS-0009` (art. 456 vs.
  art. 460) permanece bloqueada, exatamente como o handoff instruía.
- Nenhuma aprovação jurídica foi simulada para `RT-IBSCBS-0007`/`0008` (isso exige uma pessoa
  humana com responsabilidade jurídica/tributária identificada, conforme `docs/adr/0017` e o
  `ETAPA_9_1_FINAL_APPROVAL_MATRIX.md`).
- Nenhum push para GitHub ou serviço externo. O repositório é 100% local.
- `.env` não foi criado (apenas `.env.example` existe, como no pacote original).

### Estado consolidado herdado (sem alteração)

- Catálogo IBS/CBS governado: 164 `cClassTrib`, versão oficial 23/06/2026.
- Cobertura executável: **1/164 (0,61%)** — única regra real publicada: `RT-IBSCBS-0003`
  (ruleset `IBSCBS-PILOT-001`).
- `RT-IBSCBS-0007` v3 e `0008` v3: `DRAFT`, `READY_FOR_HUMAN_APPROVAL` (aguardando aprovação
  jurídica humana formal, fora do escopo de um agente).
- `RT-IBSCBS-0009` v3: `DRAFT`, `BLOCKED_LEGAL_REFERENCE_CONFLICT` (art. 456 vs. art. 460 — precisa
  de fonte oficial, não pode ser resolvido por inferência).

### Pendências desta máquina (bloqueiam etapas futuras que dependem de banco)

- [ ] Aprovar o prompt de UAC do instalador do Docker Desktop (em andamento).
- [ ] Após instalar o Docker Desktop, pode ser necessário **reiniciar o Windows** e abrir o Docker
      Desktop manualmente uma vez (aceitar termos de licença) antes de `docker compose up -d
      postgres` funcionar.
- [ ] Criar `.env` local a partir de `.env.example` e definir `DEV_SEED_PASSWORD` (nunca versionar).

## Como me orientar sobre a próxima etapa

Este projeto tem regras de governança muito rígidas (`AGENTS.md`) sobre não inventar conteúdo
tributário. Algumas continuações possíveis, dependendo do que você quer priorizar:

1. **Infraestrutura/ambiente** — concluir Docker Desktop, subir Postgres, rodar migrações e seeds,
   subir API + frontend localmente e validar via navegador (inclui o teste `postgresql_invariants`
   que hoje é pulado).
2. **Engenharia sem conteúdo jurídico novo** — atacar itens técnicos já mapeados em
   `docs/tax/IBSCBS_COVERAGE_ROADMAP.md`, `TAX_ENGINE_CONSOLIDATED_ROADMAP.md` ou dívidas técnicas
   registradas nos ADRs, sem criar regra fiscal nova.
3. **Preparar o terreno jurídico** — organizar/estruturar o que falta para as revisões humanas de
   `RT-IBSCBS-0007/0008` (não substitui a aprovação em si, que precisa ser sua ou de um responsável
   tributário identificado).
4. **Publicar no GitHub** — configurar o remoto, proteger `main`, ativar o CI já presente em
   `.github/workflows/ci.yml`.
5. Outra prioridade sua.

Aguardo sua orientação sobre qual dessas frentes seguir (ou aprove o Docker Desktop para eu
continuar a etapa de infraestrutura).

## Etapa 1 — diagnóstico do Docker/WSL2 e preparação da decisão jurídica pendente

**Data:** 2026-09-06

### Docker Desktop / PostgreSQL

O instalador do Docker Desktop concluiu (winget), mas o Docker Desktop **não consegue iniciar o
motor** nesta máquina porque o **WSL2 não está instalado** (`wsl --status` confirma "Subsistema do
Windows para Linux não está instalado"). Instalar o WSL2 exige privilégio de administrador, que
esta sessão não tem, e normalmente exige **reiniciar o Windows**.

**Ação sua, fora desta sessão:**

```powershell
wsl --install
```

Rode isso em um **PowerShell como Administrador**, reinicie o computador quando pedir, abra o
Docker Desktop uma vez (aceite os termos de licença) e aguarde o ícone da baleia ficar estável na
bandeja do sistema. Depois disso, `docker compose up -d postgres` volta a ser possível e eu
consigo concluir a etapa de infraestrutura (migrações, seeds, `test_postgresql_invariants`, subir
API + frontend).

### Priorização adotada (a seu pedido)

Como a infraestrutura ficou bloqueada por uma ação que só você pode fazer (elevação +
reinício), priorizei o item de **maior alavancagem que já estava desbloqueado**: organizar a
decisão jurídica pendente de `RT-IBSCBS-0007` e `RT-IBSCBS-0008`, que são as duas únicas
especificações hoje marcadas `READY_FOR_HUMAN_APPROVAL` sem nenhum bloqueador jurídico
remanescente. Aprová-las (se você concordar com o recorte) é o único caminho realista para sair de
**1/164 (0,61%)** para **3/164 (1,83%)** de cobertura executável, antes mesmo de qualquer nova
infraestrutura.

Não inventei, alterei ou reinterpretei nenhum conteúdo jurídico — apenas consolidei o que já
estava em `ETAPA_9_1_FINAL_APPROVAL_MATRIX.md`, nas especificações v3 e no relatório de
divergência da 0009, para você decidir com menos leitura espalhada. Percebi também que você já
está registrado como o aprovador jurídico/tributário do projeto (ator
`legal-approver-guilherme-nunes`, evidência em
`docs/tax/rules/approvals/RT-IBSCBS-0003-v2.md`), então essa decisão é sua a fazer, não algo que eu
deva ou possa substituir.

O texto completo da decisão foi enviado a você no chat desta sessão (não duplicado aqui para evitar
divergência entre as duas fontes). Resultado desta etapa:

- [ ] Aguardando sua decisão sobre `RT-IBSCBS-0007` v3 (cClassTrib `200022`).
- [ ] Aguardando sua decisão sobre `RT-IBSCBS-0008` v3 (cClassTrib `200023`).
- Nada a decidir em `RT-IBSCBS-0009` agora — permanece `BLOCKED_LEGAL_REFERENCE_CONFLICT`; a única
  ação possível é monitorar o Portal NF-e e o índice de resoluções do CGIBS por uma retificação
  oficial, o que não depende de aprovação humana.

## Etapa 2 — infraestrutura completa e stack local validada de ponta a ponta

**Data:** 2026-09-06

Você instalou o WSL2 e abriu o Docker Desktop; confirmei e conclui a etapa de infraestrutura que
ficara pendente:

1. `docker compose up -d postgres` — PostgreSQL 17 (imagem `postgres:17-alpine`) rodando em
   `localhost:5432`.
2. Criado `.env` local a partir de `.env.example`, com `DEV_SEED_PASSWORD` gerada aleatoriamente
   (24 caracteres, apenas local, fora do Git — nunca commitada).
3. `uv run alembic upgrade head` — as 6 migrações aplicaram sem erro (`0001` a `0006`).
4. **Dois bugs reais encontrados e corrigidos** ao rodar os seeds documentados pela primeira vez
   contra um Postgres real (nenhum dos dois é conteúdo tributário — são bugs de infraestrutura de
   dados; commit `04453bb`):
   - `database/seeds/development_synthetic.py` falhava com `NoReferencedTableError` porque
     `infrastructure/database/__init__.py` não importava os módulos de modelos irmãos
     (`identity_models`, `product_models`, `taxonomy_models`); qualquer script que importasse só
     `models.py` via metadados incompletos. Corrigido centralizando a importação no `__init__.py`
     do pacote.
   - `database/seeds/development_identity.py` falhava com `ForeignKeyViolation` (tentava inserir
     `companies` antes de `organizations` existir): as duas tabelas só têm coluna `ForeignKey`
     simples, sem `relationship()` ORM, e o SQLAlchemy não infere ordem de insert nesse caso.
     Corrigido replicando o padrão de `flush()` incremental já usado em
     `development_governance.py`.
5. Todos os seeds rodaram com sucesso: `development_governance.py`, `development_identity.py`,
   `development_synthetic.py`.
6. `uv run pytest` com `POSTGRES_TESTS=1`: **120 testes passaram** (o teste antes pulado,
   `test_postgresql_invariants`, agora roda e passa). Ruff e mypy continuam limpos.
7. Subi a API (`uvicorn`, porta 8000) e o frontend (`next dev`, porta 3000) em background e validei
   pelo navegador: dashboard carrega com os números reais documentados (164 cClassTrib, 163/164
   fundamentos, 1 regra publicada, cobertura 0,61%) e a tela `/login` também renderiza
   corretamente. Isso também resolve, na prática, o bloqueio de captura visual citado em
   `docs/screenshots/README.md` (o navegador seguro conseguiu abrir a aplicação nesta máquina) —
   ainda não gerei os 11 PNGs finais listados lá porque não tenho uma forma de persistir a imagem
   capturada como arquivo binário no repositório a partir desta sessão; isso pode ser feito depois
   com uma ferramenta de captura local, se você quiser fechar esse item.

### Estado local agora

- Postgres, API e frontend **rodando** nesta máquina (processos em background desta sessão).
- Acessos de desenvolvimento: `demo@example.invalid` (ADMIN) / `analyst@example.invalid`
  (ANALYST), organização `governanca-tecnica-dev`, senha em `DEV_SEED_PASSWORD` (`.env` local).
- Nenhum conteúdo tributário foi tocado nesta etapa.

### Ainda pendente (na época da Etapa 2)

- [x] Sua decisão sobre aprovar `RT-IBSCBS-0007` v3 e `RT-IBSCBS-0008` v3 — respondida e executada
      na Etapa 3, abaixo.
- [x] GitHub — autorizado e executado na Etapa 3, abaixo.

## Etapa 3 — aprovação jurídica registrada e publicação no GitHub

**Data:** 2026-09-06

Você confirmou explicitamente as duas autorizações pendentes: (1) aprovar `RT-IBSCBS-0007` v3 e
`0008` v3 como delimitado, na sua capacidade de responsável tributário/jurídico; (2) publicar o
projeto no GitHub.

### Aprovação jurídica

- `RT-IBSCBS-0007` e `RT-IBSCBS-0008` passaram de `DRAFT` para `APPROVED`, com `reviewed_by`,
  `approved_by`, `approval_date` (2026-09-06) e `approval_evidence` preenchidos nas especificações
  JSON. Evidência em `docs/tax/rules/approvals/RT-IBSCBS-0007-v3.md` e `...-0008-v3.md`, seguindo
  exatamente o formato já usado para `RT-IBSCBS-0003`. Resumo completo em
  `docs/tax/ETAPA_9_3_LEGAL_APPROVAL_P1.md` e no `README.md`.
- `RT-IBSCBS-0009` **não foi aprovada** — permanece `DRAFT`/`BLOCKED_LEGAL_REFERENCE_CONFLICT`.
- **Nenhum conteúdo jurídico foi alterado.** Nenhuma `TaxRuleVersion` foi criada, nenhum ruleset foi
  publicado. A cobertura executável **continua `1/164` (0,61%)** — aprovação documental não é
  implementação. Avaliar a implementação real de 0007/0008 exige nova autorização específica sua
  **e** a carga governada do território da Zona Franca de Manaus (`TaxJurisdictionArea`, decidido
  no ADR-0021 mas ainda sem tabela, migração ou dado real — é um pré-requisito técnico, não apenas
  jurídico).

### GitHub

- Instalado o GitHub CLI (`gh`) e autenticado via dispositivo (você aprovou o código no
  navegador duas vezes: uma para login, outra para conceder o escopo `workflow`, necessário para
  publicar `.github/workflows/ci.yml`).
- Criado o repositório **privado** `guitadeununes89-beep/ora-tributa` e feito o push de todo o
  histórico local (7 commits).
- O workflow de CI (`.github/workflows/ci.yml`, jobs `python` e `frontend`) disparou automaticamente
  e **passou** na primeira execução.
- **Não configurei proteção da branch `main`** (exigir CI e revisão antes de merge): o GitHub
  recusou com `403 — Upgrade to GitHub Pro or make this repository public to enable this feature`.
  Proteção de branch em repositório privado exige um plano pago (GitHub Team/Pro) ou tornar o
  repositório público. Fica pendente essa decisão sua, se quiser esse controle agora.

### Estado local nesta máquina

- Postgres, API (`:8000`) e frontend (`:3000`) continuam rodando em background desta sessão.
- Repositório local (`C:\Users\gtnunes\ora-tributa`) sincronizado com
  `https://github.com/guitadeununes89-beep/ora-tributa` (branch `main`).

### Pendências reais agora (na época da Etapa 3)

- [ ] Decidir se quer proteção de branch (exige plano pago ou tornar o repo público) — nenhuma
      ação minha sem sua decisão.
- [x] Nova autorização específica para avaliar implementação técnica de `RT-IBSCBS-0007`/`0008`
      — dada e executada parcialmente na Etapa 4, abaixo (só o esquema; sem dados reais).
- [ ] Monitorar fonte oficial para resolver o conflito de `RT-IBSCBS-0009` (nenhuma ação possível
      além de acompanhar).

## Etapa 4 — ADR-0024 e esquema governado de território (sem dados reais)

**Data:** 2026-09-06

Você aprovou seguir. Como implementar `RT-IBSCBS-0007`/`0008` de verdade depende do modelo de
território da ZFM (ADR-0021, ainda sem esquema), e como esse é o único item hoje verdadeiramente
acionável em direção à cobertura executável, fiz o seguinte, nessa ordem:

1. Redigi o **ADR-0024** (`docs/adr/0024-implementacao-de-areas-territoriais-governadas.md`) —
   desenho técnico do cadastro governado `TaxJurisdictionArea`/`TaxJurisdictionAreaVersion`,
   bitemporal e imutável, seguindo exatamente os mesmos padrões já usados para regras (ADR-0002,
   ADR-0009) e catálogo (ADR-0013). Você aprovou; status marcado `Aceita`.
2. Implementei **somente o esquema**, sem nenhum dado territorial real:
   - migração `0007_tax_jurisdiction_areas` (tabelas `tax_jurisdiction_areas`,
     `tax_jurisdiction_area_versions`, `tax_jurisdiction_area_lifecycle_events`, com os mesmos
     triggers de imutabilidade/append-only já usados em regras e catálogo — testei manualmente e
     nem eu consegui apagar ou alterar uma versão publicada, confirmando que o trigger funciona);
   - modelos SQLAlchemy em `infrastructure/database/territory_models.py`;
   - o **contrato do resolvedor** (porta) em `application/territory.py`
     (`TaxJurisdictionAreaResolver`), com uma implementação `NullTaxJurisdictionAreaResolver` que
     sempre retorna `UNKNOWN` — uma resposta honesta, já que nenhum dado governado existe ainda.
   - **Nenhum endpoint HTTP, nenhum CLI de carga e nenhum dado real de ZFM/ALC foi criado.**
   - Testes novos: `backend/tests/test_jurisdiction_area_invariants.py` (invariantes reais contra
     Postgres) e `backend/tests/test_territory.py` (resolvedor nulo). Ruff, mypy e os 120 testes
     Python (122 com os dois novos) continuam passando; migração aplicada com sucesso.

### O que isso NÃO faz

- **Não implementa `RT-IBSCBS-0007` nem `0008` como regra executável.** A cobertura continua
  `1/164` (0,61%). Isso ainda exige, no mínimo: carga governada de dados territoriais reais da
  ZFM/ALC (pesquisa jurídica própria — Decreto-Lei nº 288/1967, atos da Suframa e leis de cada Área
  de Livre Comércio — com o mesmo rigor de uma especificação `RT-IBSCBS`), um resolvedor real (não
  o `Null`), e então `TaxRuleVersion` + testes + publicação de ruleset.
- Não inventei nem inferi nenhum município, perímetro ou critério administrativo real.

### Achado extra: CI estava instável (corrigido)

Ao empurrar essas mudanças, o GitHub Actions revelou que `frontend: pnpm test` já falhava de forma
intermitente **antes** desta etapa, por uma causa real (não flakiness aleatória): o teste de
`assisted-consultation.test.tsx` renderizava o componente e verificava a tela sem esperar a
`Promise` do `useEffect` inicial (busca de produtos/catálogo) resolver. Quando essa promise
resolvia depois do arquivo de teste já ter sido finalizado, o Vitest já tinha destruído o ambiente
jsdom daquele arquivo, e a atualização de estado do React explodia com `window is not defined`.
Isso violava a própria regra do `AGENTS.md` (testes não devem depender de timing não controlado).

Corrigido fazendo o mock devolver um produto real (antes devolvia array vazio, indistinguível do
estado inicial) e esperando por uma consequência observável de verdade
(`await screen.findByRole("option", ...)`) antes de prosseguir com as asserções. Validado com 8
execuções locais seguidas sem erro, e confirmado verde no CI do GitHub (job `frontend` e `python`
ambos passando). Isso não tem nenhuma relação com conteúdo tributário — é higiene de teste pura.

### Nota operacional (sem impacto real)

Ao rodar a suíte com `POSTGRES_TESTS=1` várias vezes manualmente nesta sessão, o teste
`test_postgresql_invariants.py` original ficou com linhas sintéticas de teste (`PG-TEST-*`) presas
no banco local — e ficaram presas **porque o trigger de append-only realmente as protege**, nem eu
consegui apagá-las manualmente. Isso só afeta reexecuções manuais repetidas contra este Postgres
local de desenvolvimento; o CI sempre sobe um Postgres efêmero e novo, então não é afetado.

### Pendências reais agora

- [ ] Decidir se quer proteção de branch no GitHub (exige plano pago ou repo público).
- [ ] Pesquisa jurídica dedicada para carregar território real da ZFM/ALC (fonte oficial, com
      revisão e aprovação sua) — pré-requisito para qualquer resolvedor real e para publicar
      `RT-IBSCBS-0007`/`0008`.
- [ ] Monitorar fonte oficial para resolver o conflito de `RT-IBSCBS-0009`.
