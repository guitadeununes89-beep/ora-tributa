# Plataforma de Inteligência Tributária

Fundação técnica de uma plataforma auditável de inteligência, auditoria e planejamento tributário brasileiro. O primeiro domínio previsto é a Reforma Tributária (IBS, CBS e Imposto Seletivo), sem codificar regras fiscais antes de sua especificação e validação jurídica.

> **Estado atual:** catálogo oficial governado com 164 cClassTrib, lifecycle append-only, rulesets
> imutáveis e avaliações reproduzíveis. Cinco regras reais estão `PUBLISHED` — `RT-IBSCBS-0003`,
> `RT-IBSCBS-0004`, `RT-IBSCBS-0005` (medicamentos, art. 146) e `RT-IBSCBS-0007`/`RT-IBSCBS-0008`
> (Zona Franca de Manaus, art. 445/448) —, cada uma em seu próprio ruleset explícito, cobrindo 4 dos
> 164 cClassTrib (`2,44%`). São regras piloto, não representam cobertura completa, não são default
> de produção e não existe cálculo amplo da Reforma Tributária.

## Princípios centrais

- nenhuma regra é criada sem fundamento legal e fonte verificável;
- regras publicadas são versionadas e nunca sobrescritas;
- todo resultado relevante deve carregar memória de cálculo e rastreabilidade;
- valores monetários usam `Decimal`, nunca `float`;
- o motor tributário é determinístico e independente da API e da interface;
- incerteza é representada explicitamente; o sistema não força classificações;
- IA pode explicar ou apoiar a triagem, mas não substituir silenciosamente regras determinísticas.

## Arquitetura

```text
frontend (Next.js)
        │ HTTP/JSON
backend (FastAPI: casos de uso e adaptadores)
        │
tax-engine (biblioteca Python pura)
        │ portas
repositórios / base versionada de regras
        │
PostgreSQL
```

O fluxo de importação (`importers`) é separado do cálculo para permitir validação, quarentena e reprocessamento de arquivos fiscais sem contaminar o domínio.

## Estrutura

- `frontend/`: interface Next.js e TypeScript;
- `backend/`: API FastAPI e composição dos serviços;
- `tax-engine/`: tipos e contratos do domínio tributário, sem dependência da web ou banco;
- `importers/`: futuros adaptadores de XML, EFD e planilhas;
- `database/`: migrações Alembic, constraints PostgreSQL e seed sintético de desenvolvimento;
- `tests/`: testes de arquitetura e invariantes transversais;
- `docs/adr/`: decisões arquiteturais versionadas;
- `docs/`: estratégia de testes, segurança, ciclo de vida das regras e documentação técnica;
- `SPEC_PLATAFORMA_TRIBUTARIA.md`: escopo e requisitos iniciais;
- `AGENTS.md`: regras obrigatórias para pessoas e agentes de desenvolvimento.

## Pré-requisitos

- Node.js 22 LTS ou superior compatível com o Next.js declarado;
- Python 3.12 ou 3.13;
- `uv` para dependências Python;
- Docker com Compose para PostgreSQL.

Python 3.14 ainda não é o alvo de compatibilidade do projeto. Use uma das versões indicadas para evitar diferenças prematuras no ecossistema.

## Início rápido

1. Copie `.env.example` para `.env` e ajuste somente os valores locais.
2. Inicie o banco: `docker compose up -d postgres`.
3. Instale e execute a API:

   ```bash
   uv sync --all-packages --dev
   uv run alembic upgrade head
   $env:DEV_SEED_PASSWORD = "defina-uma-senha-local-segura"
   uv run python database/seeds/development_governance.py
   uv run python database/seeds/development_synthetic.py
   uv run uvicorn tributaria_api.main:app --app-dir backend/src --reload
   ```

4. Em outro terminal, instale e execute o frontend:

   ```bash
   cd frontend
   pnpm install --frozen-lockfile
   pnpm dev
   ```

5. Acesse `http://localhost:3000` e a tela técnica em `http://localhost:3000/curadoria`; a API expõe saúde em `http://localhost:8000/api/v1/health`, o endpoint sintético em `POST /api/v1/classifications/evaluate` e documentação em `http://localhost:8000/docs` apenas fora de produção. Consulte `docs/API_EXPERIMENTAL.md` antes de usar o endpoint.


### Acesso de demonstração

- frontend: `http://localhost:3000`;
- API: `http://localhost:8000`;
- OpenAPI: `http://localhost:8000/docs`;
- administração local: `demo@example.invalid` (`ADMIN`);
- consulta piloto: `analyst@example.invalid` (`ANALYST`);
- organização: `governanca-tecnica-dev`;
- senha: definida localmente em `DEV_SEED_PASSWORD`, nunca no Git.

Consulte `docs/DEVELOPMENT_ACCESS.md` para iniciar tudo após reiniciar o computador.
## Qualidade

```bash
uv run ruff check .
uv run mypy backend/src tax-engine/src importers/src
uv run pytest
cd frontend && pnpm lint && pnpm typecheck && pnpm test
```

A estratégia completa está em `docs/TESTING.md`. Decisões relevantes devem ser registradas como ADR antes da implementação. Consulte `docs/adr/README.md`.

## Git e colaboração

O repositório já está preparado para GitHub com validação contínua em `.github/workflows/ci.yml`, template de pull request e regras em `AGENTS.md`. Nenhum segredo deve entrar no Git. Recomenda-se proteger `main`, exigir revisão e tornar os checks de backend e frontend obrigatórios.

## Próximos passos seguros

1. submeter novos blocos jurídicos à pesquisa e especificação antes de criar qualquer regra;
2. evoluir a ingestão governada das tabelas oficiais complementares conforme o plano da Etapa 8;
3. implementar o modelo de objetos tributários e identificadores temporais somente após ADR e caso
   de uso aprovado;
4. preparar promoção de rulesets, segredos e observabilidade para ambientes além do desenvolvimento;
5. repetir a captura visual real em host compatível com o runtime seguro do navegador.
## Etapa 4 — identidade e organizações

A API agora possui autenticação local inicial, sessões opacas, proteção CSRF, organizações,
memberships, RBAC explícito, empresas e estabelecimentos. As telas `/login`, `/empresas`,
`/configuracoes/usuarios` e o contexto autenticado em `/curadoria` formam a interface mínima.

Para desenvolvimento, depois de aplicar as migrações, execute:

```powershell
python database/seeds/development_identity.py
```

O seed é proibido em produção e usa apenas nomes, e-mails e identificadores reservados/fictícios.
A senha de desenvolvimento deve ser trocada e nunca reutilizada. Consulte
`docs/IDENTIDADE_E_TENANCY.md`, `docs/RBAC_MATRIX.md` e o ADR 0012.


## Catálogo normativo IBS/CBS

A primeira fonte real é ingerida como catálogo consultivo governado, não como regra automática.
O artefato oficial, manifesto, hashes e documentação jurídica estão em `database/normative-artifacts`
e `docs/tax/IBS_CBS_CLASSIFICACAO.md`. A consulta web fica em
`/reforma-tributaria/classificacao`; somente snapshots publicados aparecem como conteúdo ativo.
## Etapa 6 — produtos e enquadramento assistido IBS/CBS

A plataforma agora mantém produtos isolados por organização, com snapshots imutáveis para cada
alteração tributariamente relevante. A consulta individual autenticada está em
`/reforma-tributaria/consulta` e usa `POST /api/v1/tax/ibs-cbs/classify`; cadastro, busca e histórico
estão em `/produtos`, `/produtos/novo` e `/produtos/{id}`.

O motor representa candidatos CST/cClassTrib vinculados ao snapshot publicado do catálogo,
suporte determinístico, fatos ausentes, fontes legais e `DecisionTrace`. NCM, GTIN, CEST ou descrição
nunca produzem classificação isoladamente. Como não existe especificação jurídica real `APPROVED`
em `docs/tax/rules/`, esta entrega ativa somente infraestrutura e fixtures sintéticas — nenhuma
classificação brasileira real foi implementada.

Antes da primeira regra real, preencha `docs/tax/RULE_SPECIFICATION_TEMPLATE.md`, obtenha aprovação
jurídica identificada e siga `docs/tax/rules/README.md` e `docs/tax/PRODUCT_CLASSIFICATION.md`.
## Etapa 7A — pre-flight de especificações jurídicas

A preparação da primeira regra real agora possui template JSON validável, lifecycle documental,
matriz piloto vazia e comando `validate-tax-rule-spec`. O pre-flight retorna somente
`READY_FOR_IMPLEMENTATION` ou `NOT_READY`, com problemas estruturais e de referência exatos.

A curadoria exibe o readiness dos documentos presentes em `docs/tax/rules/specifications`. No
fechamento da Etapa 7A, o diretório ainda não continha especificação jurídica real. O exemplo
`TEST-IBSCBS-0001` é fictício, fica fora desse diretório e não é executável. Consulte
`docs/tax/RULE_SPECIFICATION_TEMPLATE.md`, `docs/tax/rules/README.md` e o ADR-0015.

## Etapa 7B — primeiras especificações jurídicas reais IBS/CBS

Foram criadas as especificações jurídicas reais `RT-IBSCBS-0001`, `RT-IBSCBS-0002` e
`RT-IBSCBS-0003`, todas mantidas em `DRAFT`. A elaboração utilizou exclusivamente fontes oficiais e
registrou fundamento legal, vigência, fatos necessários, exceções e casos positivos, negativos,
inconclusivos e de limite temporal.

Os vínculos CST/cClassTrib foram preenchidos somente quando confirmados no catálogo oficial
versionado da plataforma. Identificadores persistidos, decisões interpretativas e demais pontos que
dependem de conferência permanecem explicitamente pendentes e bloqueiam a implementação.

Nenhuma `TaxRuleVersion` real foi criada ou publicada, nenhum ruleset tributário real foi publicado
e nenhuma das três especificações é executável pelo `tax-engine`. A próxima etapa obrigatória é a
revisão jurídica humana, sem promoção automática para `APPROVED`.

Consulte `docs/tax/rules/ETAPA_7B_PESQUISA_JURIDICA.md`,
`docs/tax/rules/PILOT_RULES_MATRIX.md` e
`docs/tax/rules/PILOT_RULES_VALIDATION_REPORT.md`.

## Etapa 7B.1 — saneamento das especificações piloto

A revisão jurídica intermediária resultou no saneamento das seis especificações `RT-IBSCBS-0001`
a `RT-IBSCBS-0006`, todas mantidas em `DRAFT` e sem implementação.

Foram distinguidas as entidades do art. 133, § 2º; criada a cobertura temporal completa do art. 146;
preservada a redação histórica do Anexo XIV; separadas as hipóteses dos incisos I, II e III do § 1º;
e mantidos bloqueadores explícitos para a lista do § 3º e a regulamentação sanitária de soros e
vacinas.

Os 16 testes direcionados passaram. O preflight estrutural controlado permanece `NOT_READY` por
`STATUS_NOT_APPROVED`; o comando real permanece `NOT_READY` por `REFERENCE_LOOKUP_UNAVAILABLE`,
pois o PostgreSQL e os IDs governados não estão disponíveis neste host. Nenhum ID foi inventado.

Consulte `docs/tax/rules/ART146_COVERAGE_MATRIX.md`,
`docs/tax/rules/ETAPA_7B_1_PESQUISA_OFICIAL.md` e
`docs/tax/rules/ETAPA_7B_1_VALIDATION_REPORT.md`.

## Etapa 7B.2 — resolução de referências e preparação para aprovação jurídica final

A resolução de referências foi retomada em modo fail-closed. O PostgreSQL 17.11 foi instalado
localmente, o serviço `postgresql-x64-17` está ativo em `localhost:5432` e todas as migrações foram
aplicadas até `0005_products_assisted`. O inventário governado confirmou que o banco não possui
organização, fonte legal, catálogo, versão de catálogo, CST ou cClassTrib persistidos. Por isso,
nenhum marcador foi substituído por ID inexistente.

O preflight real das seis especificações retornou `NOT_READY` com
`STATUS_NOT_APPROVED`, `SOURCE_NOT_FOUND` e `CATALOG_VERSION_NOT_FOUND`. Todas permanecem `DRAFT`.
A priorização documental é: classe A,
`RT-IBSCBS-0003`; classe B, `RT-IBSCBS-0001`, `RT-IBSCBS-0004` e `RT-IBSCBS-0005`; classe C,
`RT-IBSCBS-0002` e `RT-IBSCBS-0006`. Classe A não altera o lifecycle nem substitui a consulta das
referências: nesta execução, nenhuma regra está pronta para submissão final.

O artefato oficial local manteve o SHA-256
`1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654`, igual ao manifesto, mas
isso não prova persistência ou publicação no PostgreSQL. Consulte
`docs/tax/rules/LEGAL_APPROVAL_MATRIX.md` e
`docs/tax/rules/ETAPA_7B_2_FINAL_REVIEW_PACKAGE.md`.

Nenhuma `TaxRuleVersion` real foi criada, nenhum ruleset real foi publicado e o `tax-engine` não
teve seu comportamento produtivo alterado.

## Etapa 7B.3 — carga governada de fontes e catálogo oficial

A causa do banco normativo vazio foi identificada: migrações criavam o schema, mas os artefatos no
Git nunca haviam sido executados pelo pipeline governado. Foi criada a organização técnica fictícia
`dev-governance-org`, sem empresa real, com curador, aprovador e publicador distintos.

As fontes oficiais LC 214/2025 compilada e original, LC 227/2026 e LC 187/2021 foram preservadas com
hash e IDs governados. Os catálogos históricos 2025-12-15 e atual 2026-06-23 percorreram
`IMPORTED → VALIDATED → IN_REVIEW → APPROVED → PUBLISHED`. O snapshot atual manteve o SHA-256
`1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654`, 18 CST e 164 cClassTrib;
o histórico possui 18 CST e 145 cClassTrib. Ambos tiveram zero rejeições e zero duplicatas.

Os IDs reais foram vinculados às seis especificações, todas ainda `DRAFT`. O preflight real retorna
somente `STATUS_NOT_APPROVED`; `SOURCE_NOT_FOUND` e `CATALOG_VERSION_NOT_FOUND` foram eliminados.
A carga foi repetida com os mesmos IDs e contagens. Nenhuma `TaxRuleVersion` real ou ruleset real foi
criado, e nenhuma regra está executável pelo `tax-engine`. Consulte
`docs/tax/rules/ETAPA_7B_3_GOVERNED_LOAD_REPORT.md` e o ADR-0016.
## Etapa 7C — primeira regra tributária real

A `RT-IBSCBS-0003`, especificação versão 2, foi aprovada por responsável tributário e jurídico
humano identificado e tornou-se a primeira e única regra brasileira executável da plataforma. A
evidência de aprovação registra nome, capacidade e ator governado; CPF não foi armazenado.

A regra executável versão 1 está `PUBLISHED`, vinculada à fonte legal oficial, ao catálogo
`2295b90f-2f92-4fa4-8181-3007f02b1679`, ao CST `200` e à cClassTrib `200010`. O ruleset explícito
`IBSCBS-PILOT-001` versão `1.0.0` contém somente essa versão e possui fingerprint
`aa701a24aaded859d52af421c9765721c867cb02720a39177feef4048af4295b`. Ele não é configuração
global ou default de produção.

O motor determinístico exige confirmação de medicamento, registro Anvisa, natureza jurídica
elegível do adquirente e aquisição efetiva. Dados ausentes resultam em `NECESSITA_VALIDACAO`; fatos
incompatíveis resultam em `SEM_CLASSIFICACAO`. CNPJ, nome, descrição e NCM não substituem as provas
necessárias. A rota e a tela `/reforma-tributaria/consulta` exibem CST/cClassTrib, fundamento,
vigência, versão, catálogo, ruleset e `DecisionTrace`.

Foram validados casos positivos, negativos, inconclusivos e temporais, além da reprodução de uma
avaliação conclusiva com os mesmos hashes e resultado. As especificações `RT-IBSCBS-0001`, `0002`,
`0004`, `0005` e `0006` permanecem `DRAFT`, sem versão executável. Consulte o
`docs/tax/rules/RT-IBSCBS-0003_IMPLEMENTATION_REPORT.md` e o ADR-0017.



## Etapa 8 — experiência visual e cobertura nacional

> Esta seção descreve o estado atual. As seções das Etapas 4 a 7B acima são registros históricos do
> momento em que foram escritas; afirmações como “nenhuma regra real” não representam mais o estado
> vigente após a Etapa 7C.

A plataforma local está disponível em `http://localhost:3000`, com API em
`http://localhost:8000` e OpenAPI em `http://localhost:8000/docs`. O seed fictício usa a organização
`governanca-tecnica-dev`: `demo@example.invalid` para administração e
`analyst@example.invalid` para executar a consulta piloto. A senha é definida por
`DEV_SEED_PASSWORD` e não deve ser versionada.

A Etapa 8.1 introduziu um shell corporativo inspirado na referência visual aprovada: cabeçalho e
menu lateral azul-marinho, ações laranja, superfícies brancas, fundo cinza-claro, KPIs compactos e
tabelas azul-claro. A home apresenta a **Plataforma de Inteligência Tributária** e organiza consulta,
produtos e serviços, Reforma Tributária, cobertura normativa, empresas e curadoria. Auditoria,
planejamento e base legal permanecem marcados como “Em desenvolvimento”, sem rotas fictícias.

O catálogo `2026-06-23` possui 164 cClassTrib. O dashboard nacional registra 163 com fundamento
estruturado, 1 somente em catálogo, 159 em mapeamento jurídico, 3 com especificação DRAFT e 1 com
regra publicada. A cobertura executável é `1/164`, ou `0,61%`. A RT-IBSCBS-0003 permanece a única
regra real, somente no ruleset explícito `IBSCBS-PILOT-001`; medicamentos não são o eixo da home.

Artefatos principais:

- `docs/PRODUCT_VISUAL_REVIEW.md` — telas, perfis, navegação e avaliação de UX;
- `docs/tax/IBSCBS_NATIONAL_COVERAGE_MATRIX.md` — todos os 164 registros;
- `docs/tax/IBSCBS_COVERAGE_ROADMAP.md` — P1 a P4 por famílias oficiais;
- `docs/tax/IBSCBS_COMPLEMENTARY_TABLES_PLAN.md` — estado das tabelas adicionais;
- `docs/screenshots/README.md` — plano e bloqueador das capturas reais.

As screenshots não foram substituídas por mockups: o runtime seguro do navegador falhou ao aplicar
ACLs no sandbox Windows antes de abrir a página. A interface foi validada por HTTP, API, lint,
TypeScript, testes de componentes e build; a captura continua como limitação externa explícita.

## Etapa 9 — refino visual e primeiro bloco P1 nacional

O dashboard passa a exibir **1 regra publicada**, mantendo a natureza piloto somente no detalhe
técnico, além de destacar **163 de 164 fundamentos identificados** e a cobertura executável real de
`1/164` (`0,61%`). Os módulos prioritários foram reorganizados em cards executivos; recursos futuros
usam o badge “Em desenvolvimento” sem rotas fictícias. Cobertura permanece sob Reforma Tributária
sem alteração de URL, e links de curadoria e usuários/papéis são filtrados pelas permissões da
sessão. O cabeçalho reservou contexto para organização, empresa, estabelecimento, usuário e perfil,
sem inventar empresa ou estabelecimento selecionado.

`/reforma-tributaria/cobertura` agora apresenta as famílias oficiais com total, fundamentos
mapeados, códigos com DRAFT, aprovados, publicados, bloqueados e cobertura executável. Essas
métricas não pressupõem relação 1:1 entre cClassTrib e regra. A consulta apresenta o ponto de
entrada futuro por Produto/Mercadoria, Serviço, Direito, Operação, Importação, Exportação e Imóvel;
somente Produto/Mercadoria permanece habilitado.

O primeiro bloco P1 selecionado foi **operações com bens na Zona Franca de Manaus e em Áreas de
Livre Comércio**, cobrindo os cClassTrib `200022`, `200023` e `200024`, nos arts. 445, 448 e 463 da
LC nº 214/2025. Foram criadas `RT-IBSCBS-0007`, `RT-IBSCBS-0008` e `RT-IBSCBS-0009`, todas em
`DRAFT`, sem implementação. O preflight real retorna somente `STATUS_NOT_APPROVED` para as três.

A matriz derivada possui agora 6 códigos cujo estado mais alto é DRAFT e continua com uma única
regra publicada. Aprovação jurídica isolada não altera `0,61%`; o teto condicional seria `4/164`
(`2,44%`) somente após futura implementação testada e publicação. A divergência entre a descrição
do catálogo de `200024` (art. 456) e a remissão do art. 463, I, do texto compilado (art. 460) está
explicitamente bloqueada para revisão humana. Consulte `docs/tax/ETAPA_9_P1_SELECTION.md` e o
ADR-0020.

Nenhuma nova `TaxRuleVersion` foi criada, nenhum ruleset foi publicado e o comportamento do
`tax-engine` não foi alterado.

## Etapa 9.2 — transição tributária e Imposto Seletivo

O motor passa a reconhecer formalmente os domínios IBS, CBS, IS, ICMS e ISS, mantendo IPI, PIS,
COFINS e ICMS-ST como extensões futuras sem comportamento implícito. `TaxTransitionPeriod` e
`TaxInteractionRule` permitem representar períodos e relações de base por versões imutáveis; os
anos 2026 a 2033 não são codificados no frontend.

`TaxComputationResult` e `CalculationTrace` foram definidos com valores decimais e trilha
reproduzível. A memória de cálculo permanece separada do `DecisionTrace`: uma explica como o valor
foi obtido e a outra por que o tratamento se aplica. Ausência de regra, alíquota, interação ou fato
retorna `REQUIRES_VALIDATION`, nunca zero silencioso.

Foram documentados o calendário 2026–2033, as interações de base confirmadas, o roadmap próprio do
Imposto Seletivo e os roadmaps de ICMS e ISS. O contrato futuro de `/planejamento/transicao` e o
exemplo sintético de R$ 100.000,00 contêm estrutura, não cálculo jurídico. O menu apresenta
Classificação IBS/CBS e Cobertura Normativa, além de IS, Transição e Simulação marcados “Em
desenvolvimento”, sem rotas fictícias.

Ainda não existe cálculo amplo produtivo. Nenhuma alíquota foi inventada, nenhuma nova regra fiscal
foi publicada e a `RT-IBSCBS-0003` permanece a única regra real no ruleset piloto. Consulte
`docs/tax/ETAPA_9_2_ARCHITECTURE_REPORT.md` e o ADR-0023.

## Etapa 9.1 — revisão jurídica do primeiro bloco P1

Esta seção registra o fechamento jurídico realizado após a arquitetura paralela da Etapa 9.2; não
altera nem substitui os contratos de transição. As `RT-IBSCBS-0007`, `0008` e `0009` foram
revalidadas contra a LC nº 214/2025 compilada, a LC nº 227/2026, os regulamentos oficiais e o
catálogo cClassTrib de 23/06/2026, ainda indicado como vigente no Portal NF-e.

As três especificações foram versionadas como v3 e permanecem `DRAFT`. A 0007, delimitada ao bem
industrializado de origem nacional descrito pelo cClassTrib `200022`, e a 0008, vinculada ao
cClassTrib `200023`, estão `READY_FOR_HUMAN_APPROVAL`. A extensão regulamentar a certos bens
estrangeiros ficou expressamente fora da 0007 e não recebeu código por inferência.

A 0009 continua `BLOCKED`: a descrição oficial do cClassTrib `200024` cita habilitação pelo art.
456, enquanto o art. 463, I, da LC nº 214/2025 remete ao art. 460. Não foi localizada retificação ou
confirmação oficial que permita corrigir a divergência.

O pre-flight real das três v3 validou schema e referências governadas e retornou apenas
`STATUS_NOT_APPROVED`, como esperado para DRAFT. Nenhuma `TaxRuleVersion` foi criada, nenhum ruleset
foi alterado e a cobertura executável permanece `1/164` (`0,61%`). Consulte
`docs/tax/ETAPA_9_1_FINAL_APPROVAL_MATRIX.md`.

## Etapa 9.3 — aprovação jurídica humana de RT-IBSCBS-0007 e RT-IBSCBS-0008

O responsável tributário e jurídico do projeto aprovou integralmente as especificações v3 de
`RT-IBSCBS-0007` (cClassTrib `200022`) e `RT-IBSCBS-0008` (cClassTrib `200023`), sem alterar seu
conteúdo jurídico. Ambas passaram de `DRAFT` para `APPROVED`, com evidência registrada em
`docs/tax/rules/approvals/`. `RT-IBSCBS-0009` não foi aprovada e permanece bloqueada pelo conflito
de referência entre o art. 456 do catálogo e o art. 460 exigido pela LC nº 214/2025.

Aprovação jurídica isolada **não** cria regra executável: a cobertura permanece `1/164` (`0,61%`)
e nenhuma `TaxRuleVersion` ou ruleset foi alterado. A implementação depende de nova autorização
específica e da carga governada do território da Zona Franca de Manaus (ADR-0021). Consulte
`docs/tax/ETAPA_9_3_LEGAL_APPROVAL_P1.md`.

## Etapa 10 — território real carregado e RT-IBSCBS-0007/0008 publicadas

Com autorização específica adicional, a plataforma implementou o modelo de território governado
(ADR-0024) na prática: seis `TaxJurisdictionAreaVersion` reais estão `PUBLISHED`
(`tax_jurisdiction_areas`) — a Zona Franca de Manaus (Decreto-Lei nº 288/1967, confirmada pelo
art. 433, I, da Resolução CGIBS nº 6/2026 como abrangendo parte dos Municípios de Manaus, Rio Preto
da Eva e Itacoatiara) e as cinco Áreas de Livre Comércio oficiais (art. 437 da mesma Resolução).

`RT-IBSCBS-0007` e `RT-IBSCBS-0008` foram implementadas no `tax-engine`, testadas (54 testes novos
cobrindo cada fato obrigatório e os cenários positivos da especificação) e publicadas como
`TaxRuleVersion` reais, cada uma em seu próprio ruleset explícito
(`IBSCBS-ZFM-0007-PILOT-001` e `IBSCBS-ZFM-0008-PILOT-001`) — não um ruleset combinado, porque as
duas descrevem cenários operacionais mutuamente exclusivos. **A cobertura executável avança de
`1/164` para `3/164` (`1,83%`)**, o teto condicional já previsto em
`ETAPA_9_1_FINAL_APPROVAL_MATRIX.md`.

O resolvedor territorial (`application/territory.py`) não é chamado por nenhuma das duas regras:
todos os fatos exigidos pelas especificações (incluindo relação com a ZFM e habilitação Suframa) são
fornecidos já resolvidos por quem chama a avaliação. O resolvedor existe para uma futura
funcionalidade de apoio ao preenchimento (transformar evidência bruta nesses fatos), ainda não
construída. A interface `/reforma-tributaria/consulta` continua oferecendo apenas `RT-IBSCBS-0003`;
nenhuma mudança de frontend foi feita nesta etapa. `RT-IBSCBS-0009` continua bloqueada, sem relação
com este trabalho.
