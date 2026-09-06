# Fundamentos de segurança e privacidade

- documentos fiscais e cadastros podem conter dados pessoais, comerciais e tributários sensíveis;
- ambientes, logs, backups e relatórios deverão seguir menor privilégio e retenção definida;
- segredos nunca entram no código ou no Git;
- uploads futuros serão tratados como não confiáveis e processados em quarentena;
- parsers XML deverão desabilitar entidades externas, DTD e acesso à rede;
- multi-tenancy, autenticação e autorização exigem threat model e ADR antes da implementação;
- trilhas de auditoria devem ser protegidas contra alteração e ter acesso monitorado;
- dados de testes devem ser sintéticos ou irreversivelmente anonimizados.

Incidentes ou vulnerabilidades não devem ser publicados em issues abertas; defina um canal privado antes do lançamento externo.


## Autenticação e tenant

- Senhas locais usam Argon2id e nunca são registradas em log.
- O cookie de sessão contém token opaco aleatório; somente SHA-256 desse token é persistido.
- Cookies são `SameSite=Lax`, `HttpOnly` para a sessão e `Secure` em produção.
- Mutações autenticadas exigem o token CSRF correspondente no cabeçalho `X-CSRF-Token`.
- Falhas de login não distinguem e-mail, senha, organização ou membership inexistentes.
- O tenant e o ator vêm da sessão; aceitar esses valores do cliente é proibido.
- O seed local é bloqueado em produção e contém somente dados explicitamente fictícios.

