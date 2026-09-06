# ADR-0012 — Identidade, tenancy e autorização

- **Status:** Aceita
- **Data:** 2026-08-29
- **Relacionados:** ADR-0001, ADR-0009 e ADR-0011

## Contexto

A plataforma precisa identificar atores de forma confiável, isolar organizações e aplicar papéis
no backend antes de receber dados empresariais. Não há requisito de federação corporativa, cobrança
ou provedor externo nesta etapa. O `actor_id` declarado em comandos administrativos não oferece
autenticidade e deve ser removido dos contratos públicos.

## Decisão

### Identidade e autenticação

Adotar autenticação local mínima com:

- `users` globais, identificados por e-mail normalizado;
- credencial separada em `user_credentials`, com Argon2id e sem senha recuperável;
- sessões opacas aleatórias de 256 bits em cookie `HttpOnly`, `SameSite=Lax`, com `Secure` em
  produção;
- somente SHA-256 do token de sessão armazenado no banco;
- expiração absoluta, revogação no logout e rotação do token CSRF a cada login;
- resposta genérica para credenciais, organização ou membership inválidos, evitando enumeração.

A sessão seleciona uma `active_organization_id`. Participação em múltiplas organizações continua
modelada por memberships; troca de organização será um caso de uso posterior.

Provedores OIDC poderão substituir a verificação de credenciais sem alterar `User`, `Membership`
ou o contexto de autorização. Recuperação de senha e MFA ficam fora desta etapa.

### Tenancy

`Organization` é o tenant lógico e não usa CNPJ como identidade. `Company`, `Membership`, sessão e
novas avaliações carregam `organization_id`. `Establishment` também carrega a organização além da
empresa, permitindo chave estrangeira composta que impede associação cross-tenant no banco.

Fontes, identidades de regra, rulesets, avaliações e auditoria existentes recebem
`organization_id` anulável apenas para compatibilidade histórica. Novas gravações pelos serviços
autenticados sempre informam organização. Dados legados nulos não ficam acessíveis por endpoints
tenant-scoped sem migração explícita.

O isolamento usa três camadas: contexto autenticado, repositórios que exigem `organization_id` e
constraints/chaves compostas. Row Level Security poderá ser adicionada quando o modelo de conexão
por tenant estiver definido; não será simulada sem uma política operacional segura.

### Autorização

Usar RBAC explícito no backend:

| Papel | Permissões principais |
|---|---|
| `VIEWER` | leitura de empresas, regras e avaliações |
| `ANALYST` | leitura, avaliação e manutenção de empresas/estabelecimentos |
| `CURATOR` | criar/editar/submeter regras e criar drafts de ruleset |
| `APPROVER` | revisar e aprovar versões |
| `PUBLISHER` | publicar/retirar versões e publicar rulesets |
| `ADMIN` | gerir organização e memberships, além de leitura |

Papéis não são hierarquia implícita. Cada endpoint declara uma permissão; esconder botões no
frontend é somente apresentação. A segregação usa o `user_id` autenticado: criador, aprovador e
publicador continuam distintos quando a política estiver habilitada.

### CSRF e auditoria

Comandos autenticados por cookie exigem cabeçalho `X-CSRF-Token` igual ao cookie não-HttpOnly da
sessão e ao hash persistido. Login não exige CSRF porque cria a sessão. CORS usa origens explícitas
e credenciais.

Auditoria armazena organização, usuário autenticado, ação, alvo, instante e correlação. Nunca grava
senha, token, cookie, CNPJ completo ou conteúdo fiscal.

## Alternativas consideradas

- **OIDC/SaaS de identidade agora:** seguro e escalável, mas introduz integração, custos e
  configuração externa antes de necessidade comprovada.
- **JWT auto-contido:** dificulta revogação imediata, mudança de papel e tenant ativo; rejeitado
  para sessões administrativas.
- **Senha e sessão na mesma tabela de usuário:** rejeitado por misturar identidade e credencial.
- **Tenant vindo de header/body:** rejeitado porque permitiria troca arbitrária pelo cliente.
- **Filtro apenas na API/frontend:** rejeitado por risco de IDOR e vazamento cross-tenant.
- **Um banco por organização:** isolamento forte, porém operacionalmente prematuro.
- **ADMIN como superusuário implícito:** rejeitado; permissões são explícitas e não eliminam
  segregação jurídica.

## Consequências

Há estado de sessão no PostgreSQL e uma consulta de autenticação por requisição. Mudanças de papel
passam a valer imediatamente. Cookies exigem HTTPS em produção e proteção CSRF. A autenticação
local deverá ganhar MFA, recuperação segura, rate limiting distribuído e notificação antes de uso
produtivo.

## Critérios de revisão

Revisar antes de SSO/OIDC, MFA, recuperação de senha, RLS, acesso de suporte entre tenants,
service accounts, API pública ou multi-região.

