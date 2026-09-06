# Estratégia de testes

## Pirâmide

1. **Unidade (maior volume):** funções e invariantes do `tax-engine`, sem rede ou banco.
2. **Componentes:** serviços do backend com portas falsas e importadores com fixtures sanitizadas.
3. **Integração:** PostgreSQL real e adaptadores, isolados e executados em CI.
4. **Contrato:** OpenAPI, serialização decimal e compatibilidade frontend/API.
5. **Ponta a ponta (menor volume):** jornadas críticas com dados sintéticos.

## Matriz obrigatória para futuras regras

Cada regra fiscal terá casos:

- aplicável e não aplicável;
- imediatamente antes, no início e no fim da vigência;
- com dados completos, ausentes, contraditórios e inválidos;
- com múltiplos enquadramentos possíveis;
- com precisão e arredondamento nos limites relevantes;
- de regressão para cada defeito corrigido;
- que confirmem fundamento e versão na trilha produzida.

Fixtures devem referenciar a especificação jurídica aprovada, não apenas repetir a implementação.

## Propriedades e arquitetura

- o motor não importa frameworks/web/ORM;
- nenhum campo fiscal monetário aceita `float`;
- versões publicadas não são alteradas;
- a mesma entrada, motor e conjunto de regras produzem o mesmo resultado;
- resultado conclusivo contém regra/fonte; resultado incerto contém motivos/dados ausentes.

## Pipeline

Pull requests executam lint, tipos e testes em Python, além de lint, tipos, testes e build no frontend. A CI sobe PostgreSQL 17, executa `alembic upgrade head` e então roda os testes de integração dos triggers e adaptadores. Testes de segurança incluem dependências, segredos e análise estática conforme a infraestrutura for definida.

## Cobertura

Cobertura é sinal, não objetivo isolado. O motor deverá alcançar cobertura forte de branches e mutação futura; nenhum percentual substitui casos jurídicos revisados. Queda de cobertura em código crítico exige justificativa no pull request.


## Cobertura sintética da segunda etapa

A suíte sintética cobre os quatro estados de classificação, dados ausentes, múltiplos candidatos, ausência de correspondência, início inclusivo e fim exclusivo de vigência, regra futura, estados não publicados, supersessão, reprodução histórica, imutabilidade de snapshot, hash de conteúdo e contrato experimental da API. Nenhuma fixture representa legislação real.
## Cobertura da terceira etapa

Os testes de aplicação usam SQLite somente como adaptador rápido para workflow e transações. Cobrem criação, transições válidas e inválidas, segregação, ausência de fonte, versão publicada imutável, membro não publicado, publicação de ruleset, avaliação persistida, recuperação bitemporal e reprodução.

`test_postgresql_invariants.py` é ativado por `POSTGRES_TESTS=1` na CI, após migração real. Ele comprova append-only de eventos, snapshot publicado imutável e ruleset publicado imutável. Para executar localmente:

```bash
docker compose up -d postgres
uv run alembic upgrade head
POSTGRES_TESTS=1 uv run pytest backend/tests/test_postgresql_invariants.py
```

Todos os dados desses testes são `TEST-*` e fictícios.
## Testes da etapa de identidade

`backend/tests/test_identity_tenancy.py` cobre login válido/inválido sem enumeração, rota sem
sessão, papel insuficiente, matriz não hierárquica, isolamento entre tenants, empresa,
estabelecimento, alteração de membership e respectivos eventos de auditoria. As invariantes de
PostgreSQL permanecem na suíte de integração/CI; SQLite é usado somente para testes rápidos de
serviço e contrato HTTP.


## Cobertura da etapa 6

Os testes de produto cobrem criação, edição por nova versão, hash e histórico imutável, cópia de
atributos versionados e bloqueio cross-tenant. Os testes do motor cobrem candidato CST/cClassTrib
sintético conclusivo, múltiplos candidatos sem desempate, dado ausente, ausência de regra, limites
de vigência, regra antiga, seleção bitemporal, ruleset/fingerprint histórico e `DecisionTrace`.

O contrato assistido verifica registro OpenAPI, rejeição de catálogo não `PUBLISHED`, rejeição de
atributo tributário real sem especificação `APPROVED` e participação da versão do produto no hash do
`FactSet`. Fixtures estruturadas usam somente identificadores sintéticos e fontes `.invalid`; não
representam legislação brasileira.

A suíte PostgreSQL valida triggers quando `POSTGRES_TESTS=1`. Sem PostgreSQL migrado, esse único
teste é marcado como `skipped`; os demais devem permanecer independentes de rede e relógio real.
## Cobertura da etapa 7A

O pre-flight é testado com fixture exclusivamente `TEST-*` e lookup controlado. A matriz cobre
schema incompleto, fonte ausente, status não aprovado, catálogo inexistente/não publicado, CST e
cClassTrib inexistentes, incompatibilidade cClassTrib/CST, vigência inválida, precedência sem
fundamento e ausência de cada grupo obrigatório de casos. O único cenário `READY` usa jurisdição
sintética, URL `example.invalid` e códigos fictícios.