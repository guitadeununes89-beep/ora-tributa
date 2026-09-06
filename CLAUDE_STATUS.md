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
