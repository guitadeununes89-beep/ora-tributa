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

### Pendências reais agora (na época do fim da Etapa 4)

- [x] Decidir se quer proteção de branch no GitHub — respondido e executado na Etapa 5, abaixo.
- [ ] Pesquisa jurídica dedicada para carregar território real da ZFM/ALC (fonte oficial, com
      revisão e aprovação sua) — pré-requisito para qualquer resolvedor real e para publicar
      `RT-IBSCBS-0007`/`0008`.
- [ ] Monitorar fonte oficial para resolver o conflito de `RT-IBSCBS-0009`.

## Etapa 5 — repositório público e proteção da branch `main`

**Data:** 2026-09-06

Você optou por tornar o repositório **público** para viabilizar proteção de branch (recurso pago
em repositório privado no GitHub). Executado:

- `guitadeununes89-beep/ora-tributa` alterado de privado para **público**.
- Proteção da branch `main` ativada:
  - exige que os checks de CI `python` e `frontend` passem antes de qualquer merge (`strict:
    true`, ou seja, a branch precisa estar atualizada com `main` antes do merge);
  - exige pull request antes de integrar a `main` (`required_approving_review_count: 0`, já que
    hoje você é o único mantenedor — sem exigir aprovação de terceiro, mas ainda impedindo push
    direto sem CI);
  - bloqueia force-push e exclusão da branch `main`.

**Atenção:** como o repositório agora é público, todo o conteúdo — incluindo código, ADRs,
especificações jurídicas `RT-IBSCBS` e as evidências de aprovação com seu nome
(`docs/tax/rules/approvals/`) — é visível para qualquer pessoa na internet. Nenhum segredo real foi
commitado (`.env` nunca entrou no Git, `DEV_SEED_PASSWORD` é local); se decidir voltar a privado
depois, a proteção de branch configurada agora deixará de funcionar (mesma limitação de plano).

## Etapa 6 — pesquisa jurídica preliminar de território (ZFM/ALC)

**Data:** 2026-09-06

Você pediu para eu seguir com a "produção" e perguntou em que percentual eu avaliaria o projeto —
respondi no chat (resumo: cobertura tributária real ~0,61-1,83%; fundação de engenharia ~60-65%;
produto completo ~15-20%, puxado para baixo pelo conteúdo tributário ser o gargalo estrutural).

Comecei a pesquisa jurídica de fonte oficial para o território ZFM/ALC (pré-requisito de
`RT-IBSCBS-0007`/`0008`, conforme ADR-0024). Usei busca e leitura web, e produzi
`docs/tax/territory/ZFM_ALC_RESEARCH_MEMO.md`, marcado explicitamente como **`PESQUISA
PRELIMINAR`** — não é especificação aprovada nem dado governado, e não autoriza carregar nada em
`tax_jurisdiction_areas`.

Encontrado com razoável confiança:
- **ZFM**: Decreto-Lei nº 288/1967, arts. 1º-2º (área geográfica: 10.000 km² mínimos à margem
  esquerda dos rios Negro e Amazonas, incluindo Manaus) e art. 42 (vigência, prorrogada por
  sucessivas emendas — a mais recente, EC nº 83/2014, até 2073).
- **5 Áreas de Livre Comércio oficiais**, cada uma com sua lei de criação: Tabatinga (Lei
  7.965/1989), Guajará-Mirim (Lei 8.210/1991), Macapá e Santana (Lei 8.387/1991, art. 11), Boa
  Vista e Bonfim (Lei 8.256/1991, ampliada por Lei 15.273/2025), Brasiléia e Cruzeiro do Sul (Lei
  8.857/1994).

**Deliberadamente não resolvido** (fica explícito no memorando, para você ou um próximo passo
decidir):
- Se a LC nº 214/2025 define "ZFM" por remissão direta ao DL 288/1967 ou por conceito próprio —
  essencial antes de aprovar qualquer versão territorial real.
- Se o Executivo já alterou a configuração original da ZFM por decreto (o DL 288/1967 permite isso
  no art. 2º, § 3º) — não localizei um decreto consolidado com o perímetro atual.
- Listas mais amplas de municípios "integrantes" de cada ALC, citadas por fontes secundárias, não
  confirmadas ainda no texto literal das leis ou de decretos regulamentadores.

Nenhum dado foi carregado no banco. O próximo passo (não executado) seria ler cada fonte na
íntegra, resolver essas incertezas, e só então redigir uma especificação territorial formal para
sua aprovação — nos mesmos moldes de uma `RT-IBSCBS`.

## Etapa 7 — leitura integral da Resolução CGIBS nº 6/2026 e primeiro rascunho de especificação territorial

**Data:** 2026-09-06

Você escolheu a opção 1 (continuar lendo fontes primárias completas) e explicou o objetivo maior:
ter uma base sólida para que, quando o usuário tiver NCM, descrição de produto, dados da operação
ou até o XML, a plataforma dê uma análise confiável e completa do que ele deve fazer. Segui com
isso.

Baixei o PDF oficial da **Resolução CGIBS nº 6/2026** (252 páginas) e extraí o texto com `pypdf`
(dependência efêmera via `uv run --with pypdf`, sem instalar nada no projeto ou no sistema) para
ler os artigos 432 a 438 e 516 a 555 **na íntegra**, não por resumo de busca. Isso resolveu as três
incertezas que ficaram em aberto na Etapa 6:

- **Achado principal:** o art. 433, I da Resolução (= art. 440, I da LC nº 214/2025) é a definição
  oficial e vigente da Zona Franca de Manaus para fins de IBS/CBS: "a área definida e demarcada nos
  termos do art. 2º do Decreto-Lei nº 288/1967... **compreendendo parte dos Municípios de Manaus,
  Rio Preto da Eva e Itacoatiara**." Fonte primária direta, resolve a incerteza municipal.
- A proposta de ampliar a ZFM a 12/13 cidades da Grande Manaus é **projeto em tramitação, não lei
  em vigor** — confirmado.
- A lista oficial das 5 ALC (art. 437 da Resolução) traz lei de criação **e** decreto
  regulamentador de cada uma — inclusive dados que eu não tinha antes (ex.: Decreto nº 6.614/2008
  para Boa Vista/Bonfim, Decreto nº 1.357/1994 para Brasiléia/Cruzeiro do Sul). Confirma que as
  listas ampliadas de municípios do Acre (Acrelândia, Assis Brasil etc.) não constam da norma
  oficial vigente.
- Bônus: li o desenho completo de alíquota zero (art. 516/527, prazos de 120/210 dias),
  internamento (arts. 551-553) e **desinternamento** (art. 554, um conceito que eu não tinha
  encontrado antes e que será relevante para regras futuras).

Reescrevi `docs/tax/territory/ZFM_ALC_RESEARCH_MEMO.md` de forma consolidada (em vez de continuar
só empilhando patches) e criei o **primeiro rascunho de especificação territorial**,
`docs/tax/territory/specifications/TJA-ZFM.json`, com `status: DRAFT` e todos os campos de
aprovação nulos — espelhando exatamente o formato das especificações `RT-IBSCBS`, incluindo quatro
ressalvas documentadas em `known_conflicts` (a proposta de ampliação ainda não vigente; o DL
288/1967 não foi lido no texto consolidado original; se `effective_to` deveria ser fixado em 2073;
e que habilitação/registro Suframa é um fato separado, fora do escopo deste documento).

**Nenhum dado foi carregado em `tax_jurisdiction_areas`/`tax_jurisdiction_area_versions`.** Essa
especificação precisa da sua revisão e aprovação (mesmo processo de uma `RT-IBSCBS`) antes de
qualquer carga real.

## Etapa 8 — rascunho das 5 especificações territoriais de ALC

**Data:** 2026-09-06

Com a lista oficial do art. 437 da Resolução CGIBS nº 6/2026 confirmada (lei + decreto de cada
ALC), redigi as cinco especificações territoriais das Áreas de Livre Comércio, todas `DRAFT`:
Tabatinga, Guajará-Mirim, Boa Vista e Bonfim, Macapá e Santana, Brasiléia (com extensão a
Epitaciolândia) e Cruzeiro do Sul — em `docs/tax/territory/specifications/`, com um `README.md`
próprio explicando o fluxo de revisão (ainda manual; não existe pre-flight automatizado para
território).

Achado extra: verifiquei diretamente no texto completo já extraído da Resolução CGIBS nº 6/2026
que **"Pacaraima" não aparece em nenhuma das 252 páginas** — ou seja, a inclusão desse município na
ALC de Boa Vista pela Lei nº 15.273/2025 não está refletida no regulamento de 2026. Registrei isso
como incerteza explícita em vez de presumir a inclusão.

Cada especificação de ALC tem confiança menor que a da ZFM (só confirmei lei + decreto via art.
437; não li cada lei/decreto individual na íntegra) — isso está documentado em `known_conflicts`
de cada arquivo. Nenhuma delas desbloqueia uma regra hoje aprovada (só `RT-IBSCBS-0009`, que segue
bloqueada por outro motivo). Nenhum dado foi carregado no banco.

## Etapa 9 — aprovação jurídica das 6 especificações territoriais

**Data:** 2026-09-06

Você revisou e aprovou as 6 especificações territoriais (ZFM + 5 ALC). Registrei a aprovação
formal, na mesma capacidade e no mesmo formato usado para `RT-IBSCBS-0003`/`0007`/`0008`: um
arquivo de evidência por área em `docs/tax/territory/approvals/`, cada um **restatando
explicitamente** as ressalvas específicas daquela área (já documentadas em `known_conflicts`) como
limitações conhecidas, **não resolvidas pela aprovação** — em particular:

- Pacaraima **não** está incluído no escopo aprovado da ALC de Boa Vista (ausente do texto da
  Resolução CGIBS nº 6/2026, apesar da Lei nº 15.273/2025);
- os municípios adicionais do Acre citados por reportagens **não** estão incluídos no escopo
  aprovado da ALC de Brasiléia/Cruzeiro do Sul.

Todas as 6 especificações passaram de `DRAFT` para `APPROVED`, com `reviewed_by`, `approved_by`,
`approval_date` e `approval_evidence` preenchidos.

**O que isso não faz:** nenhuma `TaxJurisdictionAreaVersion` foi criada, nenhum dado foi carregado
em `tax_jurisdiction_areas`/`tax_jurisdiction_area_versions`, e nenhum comportamento do resolvedor
ou do motor mudou. Ainda não existe um CLI/seed governado para território — construí-lo e carregar
dados reais continuam exigindo autorização própria e específica, conforme o ADR-0024.

## Etapa 10 — carga governada real das 6 áreas territoriais (autorizado)

**Data:** 2026-09-06

Você autorizou explicitamente construir o CLI e carregar os dados reais. Executado:

1. Criado `backend/src/tributaria_api/territory_governed_load_cli.py`, espelhando o fluxo histórico
   de `real_rule_deploy_cli.py`: para cada especificação `APPROVED`, cria a identidade + versão
   (`DRAFT`), transiciona `DRAFT → IN_REVIEW → APPROVED → PUBLISHED` com um evento de lifecycle
   append-only por transição, registra evento de auditoria, e recusa rodar se a especificação não
   estiver `APPROVED` ou se `approved_by` não bater com o ator governado. Idempotente.
2. **Achado importante:** o `legal_source_id` fixo usado em todas as especificações `RT-IBSCBS-*` e
   nas territoriais (`23302183-6c92-4b34-a26d-cd272e2c1b1e`) **não existe neste banco local** — ele
   foi gerado em uma instância de banco diferente (o `create_legal_source` gera um `uuid4()` novo a
   cada primeira inserção por organização+hash). Corrigi resolvendo o `legal_source_id` da LC
   214/2025 dinamicamente por `official_url`, em vez de confiar no literal. Isso significa que este
   banco local **nunca tinha rodado `governed_load_cli.py`** nem tinha `RT-IBSCBS-0003` de fato
   implantada — só os seeds sintéticos de desenvolvimento haviam rodado até agora.
3. Rodei `governed_load_cli.py` (nunca executado antes neste banco) para carregar as fontes legais
   e o catálogo oficial — pré-requisito real, não invenção de escopo.
4. Rodei o novo carregador com `REAL_RULE_APPROVER_EMAIL` definido localmente (nunca commitado).
   **As 6 áreas estão `PUBLISHED`** no banco, com 21 eventos de lifecycle registrados. Cada
   especificação JSON teve seu campo `implementation` preenchido automaticamente pelo próprio CLI
   (mesmo padrão do `real_rule_deploy_cli.py`).
5. Suíte completa validada: JSON ok, ruff/mypy limpos, 120 testes reais passando (as 2 falhas
   observadas são a mesma poluição de dados sintéticos de execuções manuais anteriores, já
   documentada, sem relação com esta etapa). CI do GitHub voltou a ficar 100% verde.

**O que isso ainda não faz:** o resolvedor (`application/territory.py`) continua usando apenas
`NullTaxJurisdictionAreaResolver` (sempre `UNKNOWN`) — os dados territoriais existem no banco, mas
nada ainda os consulta. `RT-IBSCBS-0007`/`0008` continuam sem `TaxRuleVersion` e sem publicação —
implementá-las como regra executável (incluindo ligar o resolvedor real aos dados agora
carregados) continua sendo uma etapa separada, ainda não autorizada.

## Etapa 11 — RT-IBSCBS-0007 e RT-IBSCBS-0008 implementadas, publicadas e verificadas (autorizado)

**Data:** 2026-09-07

Você autorizou explicitamente ("pode executar então"). Implementei as duas regras no `tax-engine`,
publiquei como `TaxRuleVersion` reais, e verifiquei de ponta a ponta contra o backend/banco real —
não só os testes unitários do motor.

1. **Código**: `tax_engine/ibs_cbs_rt_0007.py` e `ibs_cbs_rt_0008.py`, com um helper compartilhado
   novo (`rule_condition_helpers.py`) — sem tocar em `ibs_cbs_rt_0003.py` (já publicada, deixada
   intocada por segurança). A lógica de internamento de 0007 usa um mapeamento de 3 estados
   (`CONFIRMED`=satisfeito, `NOT_CONFIRMED_AFTER_DEADLINE`=violado,
   `PENDING_WITHIN_DEADLINE`/`UNKNOWN`=faltante) exatamente como a narrativa da condição C05 da
   especificação descreve — não inventei simplificação.
2. **54 testes novos**, cobrindo cada fato obrigatório em todos os três caminhos (satisfeito,
   violado, faltante), os dois cenários positivos de cada regra, e os limites de vigência. Não
   copiei os casos de teste "esparsos" do próprio JSON da especificação literalmente — eles
   pressupõem fatos não listados como "fora do exemplo", não "faltantes"; montei conjuntos de fatos
   completos, no mesmo padrão já usado pelos testes de `RT-IBSCBS-0003`.
3. **Achado do mesmo tipo do território**: o `legal_source_id` e o `catalog_version_id` fixos nas
   especificações `RT-IBSCBS-0007.json`/`0008.json` também não existem neste banco (mesma causa:
   gerados em outra instância). Resolvidos dinamicamente no script de implantação
   (`real_rule_deploy_cli_p1_zfm.py`), assim como fiz para o território.
4. **As duas regras estão `PUBLISHED`** no banco (`TaxRuleVersion` reais, com proveniência
   completa e allowlist em `persisted_rule_registry.py`).
5. **Erro de design real encontrado e corrigido durante a própria verificação**: coloquei as duas
   regras inicialmente no MESMO ruleset. Ao testar de ponta a ponta contra o `EvaluationService`
   real (não só o motor isolado), descobri que isso fazia qualquer avaliação retornar sempre
   `NECESSITA_VALIDACAO`, porque 0007 e 0008 descrevem cenários mutuamente exclusivos — a regra que
   não se aplica ao caso sempre reporta seus próprios fatos como "faltantes". Corrigi criando um
   ruleset explícito por regra (`IBSCBS-ZFM-0007-PILOT-001` e `IBSCBS-ZFM-0008-PILOT-001`), no
   mesmo espírito do ADR-0017 (`IBSCBS-PILOT-001` continha só a RT-IBSCBS-0003). O ruleset combinado
   errado (`IBSCBS-ZFM-PILOT-001`) ficou publicado no banco, mas não é usado por nada — rulesets
   publicados são imutáveis, não pude apagá-lo, só parar de referenciá-lo.
6. **Verificação de ponta a ponta contra o banco real** (não só pytest): reiniciei a API, e chamei o
   `EvaluationService` real com o ruleset corrigido. Caso completo → `CONCLUSIVO`, CST 200 /
   cClassTrib 200022, todas as 14 condições satisfeitas, referência legal real anexada. Caso com
   `buyer.art_442_habilitation_status = UNKNOWN` → `NECESSITA_VALIDACAO`, com
   `missing_facts: ["buyer.art_442_habilitation_status"]` exatamente.
7. **Cobertura executável avança de `1/164` (0,61%) para `3/164` (1,83%)** — o teto condicional que
   o próprio `ETAPA_9_1_FINAL_APPROVAL_MATRIX.md` já previa.
8. CI do GitHub voltou a ficar verde após o push.

### Esclarecimento importante sobre o resolvedor

O resolvedor territorial (`application/territory.py`) **não é chamado por nenhuma das duas
regras**. Todos os fatos que as especificações exigem (inclusive relação com a ZFM e habilitação
Suframa) são fornecidos já resolvidos por quem chama a avaliação — não há, hoje, nenhum ponto do
sistema que pegue evidência bruta (endereço, CNPJ, número de inscrição Suframa) e a transforme
automaticamente nesses fatos. O resolvedor existe para essa futura funcionalidade de apoio ao
preenchimento, que ainda não foi construída. "Carregar o território" e "implementar a regra" eram,
na prática, duas peças que não dependiam uma da outra tecnicamente — mas ambas eram pré-requisitos
de governança (documentação e aprovação) antes de qualquer execução real.

### O que NÃO foi feito nesta etapa

- Nenhum resolvedor real de território foi construído (continua `NullTaxJurisdictionAreaResolver`).
- `RT-IBSCBS-0009` não foi tocada — continua bloqueada pelo conflito de referência (art. 456 vs.
  460), sem relação com este trabalho.

## Etapa 12 — tela de consulta ZFM (frontend) e verificação real no navegador

**Data:** 2026-09-07

Você pediu para eu seguir para o próximo passo. Escolhi tornar `RT-IBSCBS-0007`/`0008` de fato
usáveis: publicadas no banco (Etapa 11), mas inacessíveis, porque `/reforma-tributaria/consulta`
só conhecia a `RT-IBSCBS-0003` e o endpoint de classificação assistida tinha uma allowlist de
fatos (proteção deliberada, não descuido) que só reconhecia os 4 fatos da 0003 — qualquer fato da
ZFM seria rejeitado com HTTP 422, mesmo com a regra publicada e correta.

1. Estendi a allowlist (`contracts/assisted_classification.py`) com todos os fatos e valores
   permitidos de `RT-IBSCBS-0007`/`0008`, exatamente como aprovados nas especificações — mais 3
   testes de backend confirmando a extensão e que valores não previstos continuam rejeitados.
2. Criei `/reforma-tributaria/consulta-zfm`: nova tela com alternância entre os dois cenários
   (mutuamente exclusivos), formulário específico para os fatos de cada um, reaproveitando o
   mesmo endpoint genérico já existente (`/tax/ibs-cbs/classify`) — nenhuma mudança de endpoint foi
   necessária, ele já aceitava qualquer `ruleset_id`. Adicionei o item "Consulta ZFM (piloto)" no
   menu lateral.
3. **Verifiquei de verdade no navegador**, não só em teste automatizado: logado como
   `analyst@example.invalid`, preenchi o formulário completo da `RT-IBSCBS-0007` e recebi
   `CONCLUSIVO`, CST 200 / cClassTrib 200022, com o fundamento legal real (LC nº 214/2025, art.
   445; Resolução CGIBS nº 6/2026, art. 516) e o `DecisionTrace` completo
   (`SELECTION → EVALUATION (MATCHED) → AGGREGATION (CONCLUSIVO)`). Confirmei também que alternar
   para `RT-IBSCBS-0008` troca corretamente o formulário e o ruleset.
4. **Um bug real apareceu no caminho e foi corrigido**: a primeira tentativa de envio retornou
   HTTP 422 porque o processo da API ainda estava rodando com o código anterior à extensão da
   allowlist (sem `--reload`). Reiniciei a API — não contornei a validação.
5. Suíte completa: 177 testes Python passando, lint/typecheck/testes de frontend limpos, CI do
   GitHub verde.

Com isso, a cobertura de `3/164 (1,83%)` deixa de ser apenas um número no banco — está
efetivamente utilizável por um analista através da interface real.

## Etapa 13 — referência territorial informativa na consulta ZFM (não vinculante)

**Data:** 2026-09-07

Você pediu para eu seguir pelas duas frentes que eu havia identificado como abertas
(monitoramento da `RT-IBSCBS-0009` e um resolvedor territorial real), escolhendo a melhor forma.
`RT-IBSCBS-0009` continua sem nenhuma ação possível além de acompanhar fonte oficial (nada mudou).
Na frente territorial, decidi **não** construir um resolvedor que preenche fatos automaticamente —
os próprios specs territoriais (Etapa 7-9) documentam ressalvas como "cobre só parte do município"
(ZFM) ou "Pacaraima não confirmado no regulamento" (Boa Vista), então qualquer determinação
automática de `INSIDE`/`OUTSIDE` seria uma inferência arriscada, na contramão da regra do
`AGENTS.md` de nunca presumir fato ausente. Em vez disso, construí uma **referência informativa**:
mostra o que a base territorial governada já sabe, sem nunca decidir por quem preenche o
formulário.

1. **Backend**: novo endpoint `GET /territory/areas` (somente leitura), com repositório
   (`infrastructure/database/territory_repository.py`) que lista apenas versões territoriais já
   `PUBLISHED`, filtradas por organização. Sem caminho de escrita — carregar dado territorial real
   continua sendo função exclusiva de `territory_governed_load_cli.py`, com todo o processo de
   aprovação humana já existente. Teste novo (`test_territory_repository.py`) cobre isolamento por
   organização e filtro de status. Ruff, mypy e os 177 testes (180 com `POSTGRES_TESTS=1`) seguem
   limpos.
2. **Frontend**: a tela `/reforma-tributaria/consulta-zfm` ganhou um campo opcional "Município do
   estabelecimento (referência)". Ao digitar um município que aparece nos critérios de uma área
   governada publicada, aparece um aviso **não vinculante** citando a área, versão e dispositivo
   legal — mas nenhum campo de fato (os `<select>` ENUM) é preenchido automaticamente, e o aviso
   deixa explícito que a área pode cobrir só parte do município ou exigir comprovação adicional.
3. **Achado ao integrar os 6 specs**: as chaves de critério não são consistentes entre eles —
   `municipio_sede` (string, nas ALC de sede única), `municipios_sede` (lista, na de sede dupla) e
   `municipios_parcialmente_abrangidos` (lista, na ZFM). Tratei isso lendo as três chaves. Mais
   importante: a chave `municipio_incluido_por_lei_posterior_nao_confirmado_no_regulamento` (onde
   "Pacaraima" está guardado) foi **deliberadamente excluída** da leitura — verificado ao vivo no
   navegador que digitar "Pacaraima" não produz nenhum aviso, exatamente como a ressalva jurídica
   já registrada exige.
4. **Verificação real no navegador** (não só teste automatizado): reiniciei a API (processo antigo
   não tinha o novo endpoint), digitei "Manaus" → apareceu o aviso citando a Zona Franca de Manaus;
   digitei "tabatinga" (minúsculo, sem acento) → apareceu o aviso da ALC de Tabatinga, confirmando
   a normalização de caixa/acento; digitei "Pacaraima" → nenhum aviso, como esperado. Sem erros no
   console do navegador.
5. Dois testes novos de frontend cobrem o caso positivo e o caso negativo; suíte completa (13
   testes), typecheck e lint do frontend continuam limpos.

### O que isso NÃO faz

- Não decide, infere nem preenche `buyer.establishment_area_status`,
  `seller.establishment_zfm_relation` ou qualquer outro fato de `RT-IBSCBS-0007`/`0008` — o
  analista sempre confirma manualmente. Isso é uma escolha de design deliberada, não uma limitação
  técnica adiada: os próprios specs jurídicos aprovados dizem que uma verificação de município
  sozinha não basta.
- Não resolve `RT-IBSCBS-0009` (continua bloqueada, sem ação possível).
- Não adiciona endereço, CEP ou geometria — continua sendo comparação textual de nome de município
  contra os critérios administrativos já aprovados, exatamente o que o ADR-0021 previa como escopo.

## Etapa 14 — elo cClassTrib → ruleset consultável, e uma lacuna real corrigida (RT-IBSCBS-0003)

**Data:** 2026-09-07

Você compartilhou a descrição da e-Auditoria (módulo "Tributação na Reforma") como referência de
onde quer chegar: consulta por NCM/NBS, código ou descrição, com base legal e várias regras
(CBS/IBS/IS/IPI/II/PIS-COFINS/ICMS/ICMS-ST/Pauta Fiscal/CEST), lote de até 500 itens, leitura de
XML de NF-e/EFD, laudos com identidade visual do escritório e um simulador de regime 2027-2033.
Registrei essa visão em memória de longo prazo (fora deste repositório) para orientar priorização
futura, mas fui explícito com você de que replicar tudo isso é trabalho de vários estágios contra
um produto comercial maduro — nada disso foi (nem deveria ser) tentado numa única etapa.

Escolhi como primeira fatia concreta o elo que faltava para a consulta "por código ou descrição"
já existente (`/reforma-tributaria/cobertura` já buscava por texto, mas não dizia qual ruleset
consultar):

1. **Backend**: `GET /taxonomy/ibs-cbs/coverage` (e `/coverage/{code}`) passam a incluir, por regra
   associada a um cClassTrib, `queryable_rulesets` — os rulesets **publicados e de regra única**
   que realmente respondem por aquele código. A exigência de regra única (não só `PUBLISHED`)
   existe porque o próprio Etapa 11 já tinha descoberto e documentado que um ruleset publicado
   pode empacotar regras mutuamente exclusivas e sempre retornar `NECESSITA_VALIDACAO` — o ruleset
   abandonado `IBSCBS-ZFM-PILOT-001` continua publicado (imutável) mas nunca aparece como
   candidato, exatamente por isso. Novo teste de integração
   (`test_queryable_rulesets.py`) reproduz esse cenário exato contra Postgres real.
2. **Frontend**: no painel `/reforma-tributaria/cobertura`, cada regra associada a um cClassTrib
   publicado ganha um link **"Consultar via `<ruleset_id>` →"** apontando para a tela de consulta
   correta (`/reforma-tributaria/consulta` ou `/reforma-tributaria/consulta-zfm`, conforme um mapa
   pequeno e explícito no próprio componente — um ruleset sem entrada nesse mapa simplesmente não
   ganha link, nunca inventamos um). Testado (3 testes novos) e verificado ao vivo no navegador
   buscando por "200022" (mostrou o link certo) e "200099"/casos sem ruleset (sem link).
3. **Achado real ao testar isso no navegador, não previsto na etapa**: `RT-IBSCBS-0003`
   (cClassTrib 200010) **não estava de fato publicada neste banco Postgres local** — só as duas
   regras da ZFM (0007/0008) estavam. A tabela `rulesets` nem tinha `IBSCBS-PILOT-001`. Ou seja, a
   cobertura real aqui era 2/164, não 3/164 como as etapas anteriores registraram, e a tela
   `/reforma-tributaria/consulta` (a original, usada para 0003) quebraria se alguém tentasse usar
   nesta máquina. Avisei você antes de agir; você autorizou a correção.
4. **Correção**: `real_rule_deploy_cli.py` (o script original de implantação de `RT-IBSCBS-0003`)
   tinha o mesmo bug de portabilidade de UUID já corrigido em três lugares antes (território,
   0007/0008): `legal_source_id`/`catalog_version_id` eram literais fixos de outra instância de
   banco. Apliquei a mesma correção (resolver dinamicamente por URL oficial e por
   cclasstrib+versão do catálogo, em vez de confiar no literal) e rodei o CLI já existente —
   nenhuma decisão jurídica nova, a aprovação de `RT-IBSCBS-0003` v2 já existia desde antes desta
   sessão. Resultado: `RT-IBSCBS-0003` agora está `PUBLISHED` de verdade neste banco, ruleset
   `IBSCBS-PILOT-001` criado e publicado, cobertura real confirmada em 3/164 (1,83%) tanto no
   endpoint de cobertura quanto no dashboard.
5. Suíte completa: 178 testes Python passando (182 com `POSTGRES_TESTS=1`), ruff/mypy limpos, 18
   testes de frontend passando, typecheck/lint do frontend limpos.

### O que isso NÃO faz

- Não implementa consulta por NCM/NBS — ainda não existe tabela NCM nem mapeamento NCM→cClassTrib
  no sistema; isso é uma frente própria, maior, ainda não iniciada.
- Não lê XML de NF-e, EFD ou planilhas, não faz consulta em lote, não gera laudo/relatório
  exportável nem envia nada por e-mail — tudo isso é visão de longo prazo (e-Auditoria), não
  escopo desta etapa.
- Não expande cobertura jurídica além do que já existia (3/164 continua sendo o teto real; a
  correção desta etapa apenas tornou esse número verdadeiro no banco, não criou regra nova).

## Etapa 15 — RT-IBSCBS-0004 e RT-IBSCBS-0005 aprovadas, implementadas e publicadas

**Data:** 2026-09-07

Levantei o estado das 5 especificações DRAFT existentes (`RT-IBSCBS-0001/0002/0004/0005/0006`) e
identifiquei que só `0004` e `0005` não tinham nenhum bloqueador `NEEDS_*` pendente de fonte
externa — `0001`, `0002` e `0006` seguem bloqueadas, sem ação possível. Apresentei as duas prontas
para sua decisão; você aprovou ambas ("aprovo e pode seguir").

1. **Aprovação jurídica registrada**: as duas especificações passaram de `DRAFT` para `APPROVED`,
   com `reviewed_by`, `approved_by`, `approval_date` (2026-09-07) e `approval_evidence`
   preenchidos. Evidência em `docs/tax/rules/approvals/RT-IBSCBS-0004-v1.md` e `...-0005-v1.md`,
   seguindo o mesmo formato já usado para `RT-IBSCBS-0003/0007/0008`, restatando explicitamente as
   ressalvas já documentadas em `known_conflicts` (nenhuma lista de NCM/SH do Anexo XIV é inferida
   pela 0004; a 0005 não autoriza combinar sua regra com a do inciso I mesmo compartilhando
   cClassTrib 200010).
2. **Implementação no `tax-engine`**: `ibs_cbs_rt_0004.py` (3 condições: NCM/SH informada,
   correspondência ao Anexo XIV confirmada, versão normativa original) e `ibs_cbs_rt_0005.py` (7
   condições cobrindo medicamento, registro Anvisa, entidade de saúde, imunidade, adquirente
   efetivo, CEBAS e requisito SUS) — reaproveitando os helpers compartilhados de
   `rule_condition_helpers.py`. Vigência (01/01 a 13/01/2026, fim exclusivo, para a 0004) é
   aplicada pelo motor via `TaxRuleVersion.valid_from/valid_to`, não por condição própria da regra
   — mesmo padrão já usado por `RT-IBSCBS-0003/0007/0008`. 31 testes novos, cobrindo cada fato
   obrigatório nos três caminhos (satisfeito, violado, faltante) e os limites de vigência
   (inclusive o fim exclusivo em 14/01/2026 da 0004).
3. **Achado do mesmo tipo já visto antes, corrigido no mesmo commit**: o script de implantação
   original (`real_rule_deploy_cli.py`, usado só para `RT-IBSCBS-0003`) tinha o padrão antigo de
   validação (`TaxRuleSpecificationValidator` verificando existência de `legal_source_id`/
   `catalog_version_id` no banco a partir dos literais do JSON) em vez do padrão já corrigido nos
   scripts territoriais e de ZFM (resolução dinâmica). Reaproveitei o padrão já corrigido: novo
   script `real_rule_deploy_cli_p2_medicamentos.py` resolve `legal_source_id` por URL oficial (a
   0004 cita a publicação original da LC nº 214/2025, já carregada nesta base; a 0005 cita a
   "norma atualizada" da Câmara, que não existe nesta base — resolvida para o texto compilado do
   Planalto, já usado por `0003/0007/0008`, mesmo precedente já aplicado antes) e
   `catalog_version_id` por cClassTrib + versão do catálogo.
4. **Cada regra em ruleset explícito próprio** (`IBSCBS-PILOT-0004-001`, `IBSCBS-PILOT-0005-001`),
   nunca combinado com outro — a `RT-IBSCBS-0005` share o cClassTrib 200010 com a já publicada
   `RT-IBSCBS-0003`, mas cada uma tem seu próprio ruleset de regra única, exatamente o padrão do
   ADR-0017 e a lição da Etapa 11 (ruleset combinado sempre retorna `NECESSITA_VALIDACAO` para a
   regra que não se aplica). O elo `queryable_rulesets` construído na Etapa 14 já reflete isso
   corretamente sem nenhuma mudança adicional: a busca por "200010" no dashboard de cobertura
   agora mostra dois links de consulta distintos, um para cada regra.
5. **Verificação de ponta a ponta contra o banco real** (não só pytest): reiniciei a API, chamei
   `POST /tax/ibs-cbs/classify` diretamente para as duas novas regras. Caso completo da 0004 →
   `CONCLUSIVO`, CST 200/cClassTrib 200009. Caso completo da 0005 → `CONCLUSIVO`, CST
   200/cClassTrib 200010. Caso da 0005 com `buyer.cebas_status = UNKNOWN` →
   `NECESSITA_VALIDACAO`, `missing_facts: ["buyer.cebas_status"]` exatamente. Um 422 real apareceu
   no meio do caminho (mesmo padrão da Etapa 12: processo da API sem `--reload` ainda rodando
   código anterior à extensão da allowlist) — corrigido reiniciando a API, não contornando a
   validação.
6. **Cobertura executável avança de `3/164` (1,83%) para `4/164` (2,44%)** — `RT-IBSCBS-0004`
   soma um cClassTrib novo (200009); `RT-IBSCBS-0005` aprofunda 200010 (já contado via 0003) com
   uma segunda hipótese jurídica real, sem alterar o denominador.
7. Estendi a allowlist de fatos governados (`contracts/assisted_classification.py`) com os fatos
   de ambas as regras, e adicionei `product.ncm_sh` ao conjunto de fatos de texto livre (sem
   enumeração fechada, mesmo tratamento de `operation.zfm_area_version_id`). Testes novos
   confirmam aceitação dos fatos válidos e rejeição de valores não previstos.
8. Suíte completa: 212 testes Python passando (216 com `POSTGRES_TESTS=1`), ruff/mypy limpos, 15
   testes de frontend continuam passando (nenhuma mudança de frontend nesta etapa), CI a confirmar
   após o push.

### O que isso NÃO faz

- Não constrói nenhuma tela de consulta dedicada para `RT-IBSCBS-0004`/`0005` — hoje só são
  alcançáveis via API direta ou pelo link "Consultar via `<ruleset_id>`" no dashboard de
  cobertura (Etapa 14), que ainda não sabe abrir um formulário específico para essas duas regras
  (o mapa `RULESET_CONSULTATION_LINKS` do frontend não tem entrada para elas). Construir essa tela
  — nos mesmos moldes de `/reforma-tributaria/consulta-zfm` — é o próximo passo natural se você
  quiser usar essas regras pela interface.
- Não avança `RT-IBSCBS-0001`, `0002`, `0006` nem `0009` — todas seguem bloqueadas por fonte
  oficial ausente, sem ação possível.

## Etapa 16 — tela de consulta para RT-IBSCBS-0004/0005 e verificação real no navegador

**Data:** 2026-09-07

Você pediu para eu construir a tela de consulta que faltava para 0004/0005, mesma pendência que eu
mesmo tinha registrado ao final da Etapa 15.

1. Criei `/reforma-tributaria/consulta-medicamentos`: nova tela com alternância entre os dois
   cenários (mutuamente exclusivos, mesmo padrão de `consulta-zfm`), formulário específico para os
   fatos de cada regra, reaproveitando o mesmo endpoint genérico `/tax/ibs-cbs/classify`. O campo
   `product.ncm_sh` (NCM/SH verificada) aparece só no cenário 0004, como campo de texto livre — sem
   inferência, exatamente como a especificação exige — em vez de um `<select>` fechado. O campo de
   data da 0004 ganhou `min`/`max` (01/01 a 13/01/2026) com uma nota explicando a janela histórica
   exclusiva, para deixar visível na própria interface a limitação temporal já registrada na
   especificação.
2. Liguei o mapa `RULESET_CONSULTATION_LINKS` do dashboard de cobertura (Etapa 14) aos dois novos
   rulesets (`IBSCBS-PILOT-0004-001`, `IBSCBS-PILOT-0005-001`) — o elo "Consultar via..." construído
   naquela etapa passou a funcionar para as duas regras novas sem nenhuma outra mudança, prova de
   que aquele desenho generaliza como pretendido. Adicionei o item "Consulta Medicamentos (piloto)"
   ao menu lateral.
3. **Verifiquei de verdade no navegador**, não só em teste automatizado: logado como
   `analyst@example.invalid`, preenchi o formulário completo da `RT-IBSCBS-0004` (data 05/01/2026,
   dentro da janela) e recebi `CONCLUSIVO`, CST 200/cClassTrib 200009, com o fundamento legal real
   (LC nº 214/2025, art. 146, caput, redação original; Anexo XIV) e o `DecisionTrace` completo.
   Alternei para `RT-IBSCBS-0005`, preenchi seus 7 fatos e recebi `CONCLUSIVO`, CST 200/cClassTrib
   200010, fundamento do art. 146, § 1º, II. Confirmei também, a partir do dashboard de cobertura,
   que buscar "200009" mostra o link "Consultar via IBSCBS-PILOT-0004-001 →" apontando para a tela
   nova. Sem erros no console do navegador.
4. 2 testes novos de frontend (padrão/alternância de cenário, igual ao de `consulta-zfm`); suíte
   completa (17 testes), typecheck e lint do frontend continuam limpos.

Com isso, as quatro regras reais publicadas (`RT-IBSCBS-0003/0004/0005` e o par ZFM `0007/0008`)
estão todas alcançáveis por um analista através de uma tela real, e a descoberta "código/descrição
→ regra aplicável → formulário certo" (a fatia de "consulta por NCM/NBS" do e-Auditoria que eu
recomendei priorizar) está fechada de ponta a ponta para tudo que já está publicado hoje.

### O que isso NÃO faz

- Não avança `RT-IBSCBS-0001`, `0002`, `0006` nem `0009` — seguem bloqueadas.
- Não inicia a frente de NCM/NBS real, XML/EFD, lote ou relatório/e-mail — visão de longo prazo
  ainda não iniciada.
- Não inicia a frente de NCM/NBS nem qualquer item da visão de longo prazo do e-Auditoria.

## Etapa 17 — dashboard e topbar param de mentir sobre a cobertura

**Data:** 2026-09-07

Você pediu para eu escolher a próxima alteração. Ao revisar a interface depois da Etapa 16,
percebi que o dashboard inicial (`/`) e o indicador de cobertura no topo de toda tela
(`app-shell.tsx`) ainda mostravam **"0,61% · 1 de 164 cClassTrib · RT-IBSCBS-0003"** — números
fixos, escritos em código na Etapa 0/1, nunca atualizados nas oito etapas seguintes em que a
cobertura real avançou. Isso contraria diretamente o princípio central deste projeto (nunca
apresentar cobertura maior — ou, neste caso, **desatualizada** — do que a real): um analista
abrindo a plataforma hoje veria "0,61%" em toda página, enquanto a tela de cobertura normativa já
mostrava corretamente "2,44%".

1. Converti `app/page.tsx` (dashboard) e o indicador `topbar-indicator` de `app-shell.tsx` para
   buscar `/taxonomy/ibs-cbs/coverage` ao vivo (mesmo endpoint já usado pela tela de cobertura e
   pelo elo "Consultar via..." da Etapa 14), em vez de literais fixos. O card "Regra real
   publicada" agora conta regras distintas publicadas de verdade (hoje 5: `0003/0004/0005/0007/
   0008`) em vez de nomear uma regra específica que ficaria errada a cada nova publicação.
2. Testes atualizados para mockar o endpoint e validar o valor dinâmico (incluindo um teste novo
   dedicado a provar que o indicador do topo mostra a porcentagem real, não mais um literal).
3. **Achado real ao verificar no navegador**: depois de editar `app-shell.tsx` com o servidor de
   desenvolvimento já rodando, o Fast Refresh do Next.js deixou o efeito de busca da cobertura
   "preso" numa versão antiga do componente — o indicador do topo continuava mostrando "…"
   mesmo com a chamada retornando 200. Um recarregamento completo (não só navegação) resolveu;
   confirmei em uma aba nova, sem histórico de HMR, que o comportamento real é `2,44%` sem nenhum
   erro no console. Registro isso porque não é a primeira vez nesta sessão que uma checagem via
   navegador revela algo que os testes automatizados (que sempre partem de um processo limpo) não
   pegariam sozinhos.
4. Sua sessão expirou durante a verificação (cookie de autenticação) — reautentiquei como
   `analyst@example.invalid` para confirmar o resultado logado.
5. Suíte completa do frontend: 18 testes passando, typecheck e lint limpos. Backend inalterado
   nesta etapa (212 testes Python continuam passando).

### O que isso NÃO faz

- Não muda nenhuma regra jurídica nem dado de cobertura — apenas corrige a interface para refletir
  o que já era verdade no banco desde a Etapa 15.
- Não resolve `RT-IBSCBS-0001/0002/0006/0009` nem inicia a frente de NCM/NBS.

## Etapa 18 — documentação do projeto parou de contradizer o banco real

**Data:** 2026-09-07

Continuando a mesma limpeza de honestidade da Etapa 17, verifiquei se a documentação do projeto
(não só a interface) também tinha números desatualizados. Encontrei dois documentos "vivos" (sem
data/versão fixando-os como registro histórico) ainda dizendo `0,61%`/`1/164`/"RT-IBSCBS-0003 é a
única regra":

1. **`README.md`**: o bloco `> **Estado atual:**` no topo do arquivo — a primeira coisa que
   qualquer pessoa (ou sessão futura do Claude) lê sobre o projeto — ainda descrevia só a
   `RT-IBSCBS-0003`. Atualizei para citar as 5 regras publicadas e `2,44%` (4/164). O restante do
   README é um log cronológico por etapa (igual a este arquivo) e **não foi tocado** — cada seção
   "Etapa N" registra o que era verdade naquele momento, e alterar esses números retroativamente
   destruiria o próprio histórico.
2. **`docs/tax/IBSCBS_NATIONAL_COVERAGE_MATRIX.md`**: matriz de 164 linhas gerada por
   `coverage_report_cli.py` (ferramenta já existente, não escrita nesta etapa). Rodei o CLI contra
   o banco real e o arquivo se corrigiu sozinho — inclusive um `catalog_version_id` desatualizado
   no cabeçalho (mesmo padrão de UUID não portátil já visto várias vezes nesta sessão) e as 4 linhas
   de cClassTrib (`200009/200010/200022/200023`) que agora mostram `PUBLISHED` com a regra e o
   ruleset corretos.
3. **Verifiquei antes de mexer** que outros documentos com os mesmos números
   (`CLAUDE_HANDOFF.md`, `docs/tax/TAX_ENGINE_CONSOLIDATED_ROADMAP.md`,
   `SPEC_PLATAFORMA_TRIBUTARIA.md`, ADRs e relatórios `ETAPA_9_*`) são explicitamente datados ou
   auto-declarados como registro histórico ("Estado em 2026-09-03", "não devem ser interpretadas
   isoladamente como estado corrente") — **não toquei nesses**, pelo mesmo motivo que não altero
   seções antigas deste arquivo.
4. Suíte completa revalidada (212 testes Python) sem nenhuma mudança de código nesta etapa — só
   documentação e um artefato gerado.

### O que isso NÃO faz

- Não estende `SPEC_PLATAFORMA_TRIBUTARIA.md` até a etapa atual — esse documento parece ter sido
  substituído por este arquivo (`CLAUDE_STATUS.md`) como log corrente; estendê-lo seria escopo novo,
  não uma correção.
- Não resolve `RT-IBSCBS-0001/0002/0006/0009` nem inicia a frente de NCM/NBS.

## Etapa 19 — confirmação de que o Anexo XIV foi revogado, e a tela deixa isso explícito

**Data:** 2026-09-07

Você apontou que o Anexo XIV foi revogado e substituído por uma classificação dinâmica — observação
correta e já era exatamente o motivo documentado do bloqueio da `RT-IBSCBS-0002` (`known_conflicts`
já registrava isso desde a Etapa 6/9.1). Fiz uma pesquisa nova em fonte oficial para confirmar se
esse bloqueio continua válido hoje, e ajustei a interface para deixar isso muito mais visível do
que estava.

1. **Pesquisa em fonte oficial (2026-09-07)**: consultei diretamente `cgibs.gov.br/atos-conjuntos`
   e li o conteúdo real dos 6 atos conjuntos/portaria publicados entre janeiro e agosto de 2026
   (baixei e extraí o PDF da Portaria Conjunta MF/CGIBS nº 7 com `pypdf`, mesma técnica já usada na
   Etapa 7 para a Resolução CGIBS nº 6). **Nenhum deles publica a lista do art. 146, § 3º** — nº 7
   trata de reconhecimento de disposições comuns CBS/IBS, nº 4 trata de amostra grátis de
   medicamento, nº 6 trata de isenção de cadastro/documento fiscal para nanoempreendedor. Notícias
   do setor (CMED, Trench Rossi Watanabe) confirmam que o prazo para entidades de classe
   submeterem a planilha ao Ministério da Saúde era 07/08/2026, mas o ato oficial com a lista em si
   ainda não foi localizado publicado até a data desta pesquisa. **O bloqueador
   `NEEDS_ART146_PAR3_OFFICIAL_LIST` continua válido** — registrei essa verificação datada em
   `known_conflicts` de `RT-IBSCBS-0002.json` para a próxima sessão não precisar refazer a mesma
   pesquisa do zero.
2. **Frontend**: a tela `/reforma-tributaria/consulta-medicamentos`, no cenário `RT-IBSCBS-0004`,
   ganhou um aviso proeminente (antes só havia a restrição discreta de `min`/`max` no campo de
   data): explica que o Anexo XIV foi revogado em 14/01/2026, que a regra só vale para operações
   dentro da janela histórica, que qualquer data posterior sempre retorna "sem classificação" por
   esta regra, e que a hipótese sucessora (`RT-IBSCBS-0002`, lista dinâmica) ainda não está
   implementada porque a lista oficial não foi publicada. O aviso desaparece corretamente ao
   alternar para `RT-IBSCBS-0005`.
3. Teste novo cobrindo a presença/ausência do aviso por cenário; suíte completa do frontend (18
   testes) e do backend (212 testes) revalidada — nenhuma mudança de regra jurídica, só
   documentação e clareza de interface.

### O que isso NÃO faz

- Não implementa `RT-IBSCBS-0002` — continua bloqueada até que o ato oficial com a lista dinâmica
  seja publicado e localizado. Isso não depende de mais pesquisa (já fiz o que dava para fazer com
  as fontes públicas disponíveis); depende de o próprio ato existir.
- Não resolve `RT-IBSCBS-0001/0006/0009` nem inicia a frente de NCM/NBS.

## Etapa 20 — nova pesquisa oficial nos três bloqueadores restantes (`RT-IBSCBS-0001/0006/0009`)

**Data:** 2026-09-08

Nesta sessão passei a ter acesso a busca e leitura web ao vivo (não tinha antes — as avaliações
anteriores de "bloqueada, só monitorar" para `RT-IBSCBS-0001/0006/0009` foram feitas sem essa
ferramenta). Com a capacidade nova disponível, refiz a pesquisa dos três bloqueadores restantes
para confirmar se algo mudou, em vez de simplesmente repetir a mesma conclusão de memória.

1. **`RT-IBSCBS-0009`** (conflito art. 456 vs. art. 460 no cClassTrib 200024): consultei a tabela
   oficial ao vivo no portal nacional da NF-e e o Informe Técnico 2025.002 vigente (v1.60,
   22/06/2026) — o texto do código 200024 continua citando art. 456, sem retificação localizada.
   Achado circunstancial que reforça a suspeita (mas não a confirma oficialmente): o art. 456 está
   no capítulo da Zona Franca de Manaus (arts. 439–457), não no capítulo das Áreas de Livre
   Comércio (arts. 458–470) a que pertence o código 200024 — compatível com um erro de remissão,
   mas isso é inferência minha, não correção oficial. **Bloqueador continua válido.**
2. **`RT-IBSCBS-0006`** (regulamentação sanitária de soro/vacina): nenhuma fonte oficial ou
   especializada localizada define critério sanitário específico para essa classificação; o Anexo
   XIV apenas relaciona itens por princípio ativo/NCM, sem regulamento autônomo. **Bloqueador
   continua válido**, junto com o mesmo bloqueador da lista dinâmica do § 3º já confirmado na
   Etapa 19.
3. **`RT-IBSCBS-0001`** (definição da "pessoa jurídica" do art. 133, § 2º): aqui encontrei algo
   mais concreto — múltiplas fontes doutrinárias (escritórios tributários, consultorias)
   convergem em interpretar essa pessoa jurídica como **a indústria ou o importador do
   medicamento**, não o mero fornecedor/distribuidor da operação (salvo se ele próprio fabricar ou
   importar). **Isso não é fonte oficial primária** — é doutrina, não decisão jurídica sua — mas é
   um insumo concreto que pode acelerar sua própria análise, se você concordar com essa leitura.
4. Registrei as três verificações datadas em `known_conflicts` das respectivas especificações,
   para a próxima sessão não repetir a mesma pesquisa do zero. Nenhuma mudança de código; suíte
   completa (212 testes) revalidada.
5. **CI quebrou depois do push** (`pnpm test` com `window is not defined` após o encerramento do
   ambiente de teste) — mesmo padrão de bug já visto e corrigido na Etapa 4, agora em
   `app-shell.test.tsx`: três dos quatro testes só esperavam a atualização de identidade, não o
   efeito independente da porcentagem de cobertura adicionado na Etapa 17, então esse efeito podia
   resolver depois do jsdom do arquivo já ter sido destruído. Corrigido fazendo cada teste também
   esperar o texto da cobertura antes de terminar; não reproduzi o bug localmente (mesma
   intermitência do episódio original), só o log do CI revelou. Novo push, CI verde de novo.

### O que isso NÃO faz

- Não desbloqueia nenhuma das três regras — permanecem `DRAFT`. `0006` e `0009` seguem sem nenhuma
  ação possível além de monitorar; `0001` tem, pela primeira vez, um insumo doutrinário concreto
  que só você pode decidir se aceita como base da definição jurídica exigida.
- Não inicia a frente de NCM/NBS nem qualquer item da visão de longo prazo do e-Auditoria.

## Etapa 21 — Consulta unificada e composição segura de regras

**Data:** 2026-09-08
**Decisão arquitetural:** [ADR-0025](docs/adr/0025-avaliacao-multirregra-e-selecao-de-candidatos.md).
**Deliverable completo:** [docs/tax/ETAPA_21_UNIFIED_RULE_EVALUATION.md](docs/tax/ETAPA_21_UNIFIED_RULE_EVALUATION.md)
(diagnóstico, solução, testes, regras preservadas, riscos remanescentes — não repetido aqui na
íntegra).

Você apontou que o Anexo XIV (usado pela RT-IBSCBS-0004) foi revogado e substituído por uma
classificação dinâmica, o que reabriu a questão de fundo já registrada como limitação na Etapa
11: a plataforma só sabia avaliar "uma regra por vez" porque combinar RT-IBSCBS-0007 e
RT-IBSCBS-0008 no mesmo ruleset sempre produzia `NECESSITA_VALIDACAO`, mesmo quando só uma das
duas hipóteses fazia sentido para o cenário. Esta etapa resolveu essa limitação na raiz, sem
tocar em nenhuma das 5 regras reais publicadas.

1. **Diagnóstico confirmado no motor:** `TaxEngine.evaluate()` agrega `missing_facts` como união
   de todas as regras `REQUIRES_VALIDATION` do ruleset, sem distinguir "regra errada para este
   cenário" de "regra certa, fato faltando" — comportamento deliberado do ADR-0008, correto para
   uma regra só, errado para hipóteses mutuamente exclusivas combinadas.
2. **Solução:** novo módulo `tax_engine.multi_rule_evaluation` (motor duplicado, não modifica
   `engine.py`) com `RuleCandidacyStatus` (SUPORTADA / escopo confirmado mas incompleto / escopo
   ainda não confirmado / não aplicável), calculado a partir da `RuleDecision` já existente de
   cada regra e de um novo registro `rule_scope_registry.py` (fail-closed, uma entrada revisada
   por regra real). Só regras com escopo confirmado e incompleto contribuem fatos faltantes ao
   resultado agregado — é isso que corrige o bug. `ClassificationStatus` continua com os mesmos 4
   valores.
3. **Backend:** migração `0008_composed_evaluations` (`ruleset_id` aceita nulo,
   `composed_ruleset_ids` novo, aplicada tanto no banco de testes quanto no de demonstração, sem
   perda de nenhuma das 11 avaliações já existentes), `EvaluationService.evaluate_many()`, e o
   endpoint aditivo `POST /tax/ibs-cbs/classify-unified`. O endpoint antigo `/classify` não mudou.
4. **Resolução de referência governada centralizada:** os 4 CLIs de implantação (que desde as
   Etapas 10/14/15 duplicavam sua própria correção de UUID não-portável) agora importam
   `governed_reference_resolution.py`, que também passou a validar `content_hash` de forma
   obrigatória antes de vincular uma fonte legal — sem tocar nas especificações JSON já aprovadas
   (isso invalidaria o hash de aprovação já registrado).
5. **Frontend:** `/reforma-tributaria/consulta` agora serve o fluxo unificado
   (`unified-consultation.tsx`): checkboxes das 5 regras reais, campos dinâmicos deduplicados por
   fato, e uma seção nova mostrando o status de cada regra na composição (inclusive "para
   considerar esta hipótese, confirme: ..." quando o escopo ainda não foi confirmado). O
   componente antigo, exclusivo de RT-IBSCBS-0003, foi removido por estar totalmente substituído.
   `/consulta-zfm` e `/consulta-medicamentos` continuam exatamente como estavam.
6. **Testes:** 11 novos no tax-engine, 4 novos arquivos no backend (`test_evaluate_many.py`,
   `test_unified_classification.py`, `test_governed_deploy_cli_fresh_database.py`,
   `test_governed_reference_resolution.py`), 4 novos no frontend — 234 testes Python e 21 testes
   de frontend passando, `ruff`/`mypy`/`pnpm lint`/`pnpm typecheck`/`pnpm build` todos limpos.
7. **Demonstração ao vivo** (login `analyst@example.invalid`, banco de demonstração real): RT-0007
   isolada → `CONCLUSIVO` limpo; RT-0007+RT-0008 compostas com só os fatos da 0007 → `CONCLUSIVO`
   (a prova viva de que o bug da Etapa 11 está corrigido, não mais `NECESSITA_VALIDACAO`), com
   RT-0008 explicitamente listada como pendente; RT-0003+RT-0005 compostas com só os fatos da 0003
   → `CONCLUSIVO` com um único candidato (sem duplicar o cClassTrib 200010 compartilhado). As três
   avaliações compostas foram persistidas corretamente no banco de demonstração.
8. **Auditoria de segurança do repositório público** (item 8 da especificação desta etapa, agente
   dedicado): nenhum segredo real, credencial ou dado pessoal sensível encontrado. Dois pontos
   levantados para sua decisão, não corrigidos automaticamente: (a) seu nome completo aparece
   como `display_name` literal em 4 CLIs e vários documentos de aprovação, como identidade do
   aprovador jurídico governado — o e-mail correspondente nunca é hardcoded; (b) a senha
   placeholder `tributaria` do Postgres local aparece igual em `docker-compose.yml`/CI/`.env.
   example`, sempre apontando para `localhost`/contêiner efêmero. Detalhes completos no
   deliverable da etapa.
9. **CI atualizado** (`.github/workflows/ci.yml`) para também implantar as 5 regras reais no banco
   efêmero do job antes dos testes — sem isso, os testes novos de nível serviço/API nunca
   exerceriam as regras reais em CI, apenas fariam skip.

### O que isso NÃO faz

- Não cria nenhuma regra tributária nova nem aprova interpretação jurídica nova.
- Não altera o conteúdo, a versão ou a aprovação de nenhuma das 5 regras reais publicadas, nem
  apaga ou modifica o ruleset combinado histórico `IBSCBS-ZFM-PILOT-001`.
- Não introduz precedência tributária entre candidatos de chaves diferentes (continua retornando
  `POSSIBLE_MATCHES` sem desempate arbitrário).
- Não inicia cálculo financeiro amplo da Reforma Tributária.
- Não resolve `RT-IBSCBS-0001/0002/0006/0009` — permanecem exatamente como estavam ao final da
  Etapa 20.
- Não altera a visibilidade do repositório nem apaga histórico de commits.
