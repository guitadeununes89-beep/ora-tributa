# Identidade, autorização e isolamento por organização

Esta fundação implementa identidade local apenas para desenvolvimento controlado e para os
primeiros fluxos do produto. Ela não contém regra tributária real.

## Modelo

- `users` representa a identidade global; credenciais permanecem separadas em
  `user_credentials` e usam Argon2id.
- `organizations` é a fronteira de tenant.
- `memberships` vincula usuário, organização e um único papel explícito.
- `auth_sessions` mantém a organização ativa, expiração, revogação, hash do token opaco e hash
  do token CSRF. O token de sessão em texto puro existe apenas no cookie `HttpOnly`.
- empresas e estabelecimentos carregam `organization_id`; todas as consultas da API usam o
  tenant obtido da sessão, nunca um identificador livre do corpo ou cabeçalho.

Papéis: `VIEWER`, `ANALYST`, `CURATOR`, `APPROVER`, `PUBLISHER` e `ADMIN`. Eles não formam uma
hierarquia implícita. A matriz em `application/security.py` é a fonte técnica das permissões.
Assim, `ADMIN` não aprova nem publica regras por consequência automática de seu nome.

## Sessão e proteção de requisições

O login recebe e-mail, senha e slug da organização. Falhas usam a mesma resposta pública para
evitar enumeração. Requisições de alteração exigem cookie de sessão e a correspondência entre o
cookie CSRF e o cabeçalho `X-CSRF-Token`. Em produção os cookies são marcados `Secure`.

Os identificadores de ator vêm exclusivamente do contexto autenticado. Clientes não podem
informar `actor_id` nos comandos administrativos.

## Limites desta etapa

OIDC/SSO, MFA, recuperação de senha, convites, rotação ampla de credenciais e Row Level Security
ficam para ADRs próprios. O isolamento atual combina chaves/constraints no banco e filtros
obrigatórios de repositório. Antes de operação SaaS pública, a adoção de RLS deverá ser reavaliada.

