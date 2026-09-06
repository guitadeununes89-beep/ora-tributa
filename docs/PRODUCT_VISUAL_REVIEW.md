# Revisão visual do produto — Etapa 8.1

## Direção visual aplicada

A interface adota a estrutura corporativa da referência fornecida: barra superior azul-marinho,
menu lateral persistente, fundo de trabalho cinza-claro, superfícies brancas, tabelas com cabeçalho
azul-claro e laranja para ação e destaque. A marca da referência não foi copiada; a identidade
própria `Ora Tributa` identifica a Plataforma de Inteligência Tributária.

O sistema deixou de usar uma apresentação editorial centrada em medicamentos. Medicamentos aparecem
somente no escopo explícito da regra piloto RT-IBSCBS-0003. O universo principal é o catálogo
nacional de 164 cClassTrib.

## Mapa de navegação

```text
Dashboard
├── Consulta Tributária
├── Produtos e Serviços
│   ├── Novo cadastro
│   └── Detalhe e histórico
├── Reforma Tributária
│   ├── Catálogo CST/cClassTrib
│   └── Cobertura Normativa
├── Empresas
├── Curadoria
└── Usuários e Papéis

Em desenvolvimento, sem rota fictícia:
Auditoria · Planejamento Tributário · Base Legal
```

## Inventário real de telas

Os perfis abaixo refletem a autorização da API. A interface não substitui o controle do backend.

| Rota | Título | Finalidade | Perfil autorizado | Estado |
|---|---|---|---|---|
| `/` | Dashboard | visão nacional, indicadores e acesso aos módulos | público; contexto adicional quando autenticado | funcional |
| `/login` | Entrar na plataforma | autenticação por usuário e organização | público | funcional |
| `/empresas` | Empresas | consultar empresas; cadastrar quando autorizado | leitura: autenticados; escrita: `ADMIN` | funcional |
| `/produtos` | Produtos e serviços | consultar cadastros versionados | perfis com `READ` | funcional |
| `/produtos/novo` | Novo produto | cadastrar objeto fictício ou real da organização | `ADMIN` (`MANAGE_COMPANY`) | funcional |
| `/produtos/{id}` | Detalhe do produto | snapshot atual e histórico de versões | perfis com `READ` | funcional |
| `/reforma-tributaria/classificacao` | CST IBS/CBS e cClassTrib | consultar catálogo oficial publicado | perfis com `READ` | funcional |
| `/reforma-tributaria/consulta` | Consulta individual | executar o ruleset piloto e exibir evidências | `ANALYST` (`RUN_EVALUATION`) | funcional no escopo piloto |
| `/reforma-tributaria/cobertura` | Cobertura normativa IBS/CBS | consultar 164 códigos, estados, vínculos e histórico | perfis com `READ` | funcional |
| `/curadoria` | Curadoria tributária | prontidão e lifecycle governado | leitura autenticada; mutações conforme `CURATOR`, `APPROVER` e `PUBLISHER` | funcional |
| `/configuracoes/usuarios` | Usuários e papéis | consultar e alterar memberships | `ADMIN` | funcional |

Não existe rota `/reforma-tributaria/historico`. Os identificadores reproduzíveis são exibidos na
consulta e persistidos pela API. Auditoria, planejamento e base legal aparecem como módulos futuros,
sem links para páginas vazias.

## Validação operacional real

Em 01/09/2026, com PostgreSQL, FastAPI e Next.js locais ativos:

- home e login redesenhados responderam HTTP `200`;
- as rotas frontend existentes foram compiladas pelo build do Next.js;
- autenticação de `ADMIN` e `ANALYST` foi validada;
- o dashboard de cobertura retornou 164 cClassTrib e `0,61%` de cobertura executável;
- o detalhe `200010` retornou duas especificações, uma regra publicada e dois snapshots históricos;
- o cenário positivo da RT-IBSCBS-0003 retornou `CONCLUSIVO`, CST `200`, cClassTrib `200010`, três
  passos de `DecisionTrace` e snapshot do produto;
- evidências desconhecidas retornaram `NECESSITA_VALIDACAO`, com fatos ausentes explícitos;
- nenhuma regra nova foi publicada.

## Pontos fortes

- navegação transversal consistente em todas as páginas;
- contraste forte entre estrutura, ação e conteúdo;
- indicadores nacionais visíveis sem inflar cobertura;
- estados fiscais e incertezas mantêm semântica própria;
- módulos futuros são identificados sem criar rotas fictícias;
- layout responsivo com menu lateral recolhível em telas menores.

## Problemas e inconsistências identificados

- o modelo técnico ainda se chama `Product`, apesar da terminologia visual “Produtos e Serviços”;
- a home utiliza indicadores estáticos coerentes com o snapshot atual; o dashboard de cobertura é a
  fonte dinâmica e deve substituir esses resumos quando houver novo snapshot;
- não há tela dedicada ao histórico de avaliações;
- o cadastro ainda não modela NBS e identificadores temporais como coleção governada;
- não há dados auditáveis de participação econômica para priorização por mercado.

## Melhorias aplicadas

- shell corporativo com cabeçalho, identidade, sessão e logout;
- menu lateral com estado ativo e módulos futuros;
- home convertida em dashboard compacto;
- login redesenhado;
- paleta marinho, laranja, cinza-claro, branco, azul, verde e vermelho aplicada globalmente;
- formulários, cards, tabelas, catálogo, consulta e cobertura harmonizados pelo mesmo design system;
- terminologia da navegação alterada para bens, serviços e demais objetos tributários.

## Melhorias futuras

- derivar os KPIs da home do endpoint de cobertura;
- criar histórico consultável de avaliações e revisões;
- implementar `TaxObject` e identificadores temporais conforme ADR-0019;
- realizar testes formais de acessibilidade e navegação por teclado;
- capturar evidências visuais em ambiente no qual a automação segura do navegador consiga iniciar.

## Screenshots

A captura real voltou a ser tentada nesta etapa. O runtime seguro do navegador encerrou antes de
abrir a página porque o sandbox Windows não conseguiu aplicar suas ACLs
(`helper_unknown_error: apply deny-read ACLs`). A aplicação permaneceu acessível por HTTP e os
componentes foram validados por lint, TypeScript, testes e build.

Nenhum mockup foi apresentado como screenshot da aplicação. A pendência e a lista mínima de
capturas estão em `docs/screenshots/README.md`.
