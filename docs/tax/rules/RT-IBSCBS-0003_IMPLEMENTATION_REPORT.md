# Relatório de implementação — RT-IBSCBS-0003

## 1. Resultado

A especificação jurídica `RT-IBSCBS-0003`, versão 2, é a primeira e única regra tributária real
executável da plataforma. A aprovação jurídica humana foi registrada em 31/08/2026. A identidade
da pessoa aprovadora foi governada pelo identificador `legal-approver-guilherme-nunes`, com a
capacidade declarada de responsável tributário e jurídico do projeto. Nenhum CPF foi persistido
como evidência de aprovação.

As especificações `RT-IBSCBS-0001`, `0002`, `0004`, `0005` e `0006` permanecem `DRAFT`, sem
`TaxRuleVersion` e fora de qualquer ruleset real.

## 2. Evidência e especificação aprovadas

- especificação: `docs/tax/rules/specifications/RT-IBSCBS-0003.json`;
- versão da especificação: `2`;
- status: `APPROVED`;
- evidência: `docs/tax/rules/approvals/RT-IBSCBS-0003-v2.md`;
- SHA-256 da evidência: `fb53804622dd94a5a753c9b3d308a65192e277068df5be170bd50b33d6e0a7f6`;
- hash canônico da especificação aprovada, desconsiderando apenas o vínculo de implementação:
  `b9cc6fb44c3f2f7ee84f91eba30f93b99ad3dfac9976d0ee809489af89cf29db`;
- pre-flight: `READY_FOR_IMPLEMENTATION`, sem issues.

A exceção de acumulação das funções de revisão e aprovação jurídica pela mesma pessoa foi aceita
somente para esta especificação piloto. Criação técnica, aprovação da versão executável e
publicação continuaram registradas separadamente conforme o ADR-0017.

## 3. Proveniência persistida

| Elemento | Valor |
|---|---|
| `TaxRuleIdentity.id` | `7e0c67f5-0a8c-46c4-94ea-c9f258ef2e67` |
| `TaxRuleVersion.id` | `56322ae2-aa2a-4d7d-8af0-d8b348953c0e` |
| versão executável | `1` |
| lifecycle | `PUBLISHED` |
| vigência | desde `2026-01-01`, sem término cadastrado |
| fonte legal | `23302183-6c92-4b34-a26d-cd272e2c1b1e` |
| catálogo publicado | `2295b90f-2f92-4fa4-8181-3007f02b1679` |
| CST | `200` |
| cClassTrib | `200010` |
| implementação | `REAL_RT_IBSCBS_0003_V1` |
| hash da versão | `508e3781d2c9177a7509bd7b959af51d6a7e3660d3601a7388cc498e73288d1a` |

O PostgreSQL está migrado até `0006_first_real_tax_rule`. A versão persistida referencia a
especificação, fonte legal, catálogo, CST e cClassTrib por chaves governadas reais.

## 4. Lifecycle e segregação técnica

O histórico imutável contém:

1. `DRAFT → IN_REVIEW`, ator técnico `dev-curator`;
2. `IN_REVIEW → APPROVED`, ator jurídico `legal-approver-guilherme-nunes`;
3. `APPROVED → PUBLISHED`, ator técnico `dev-publisher`.

Os eventos de auditoria equivalentes incluem criação da identidade, criação da versão, submissão,
aprovação, publicação, criação/publicação do ruleset e as avaliações reais executadas.

## 5. Motor determinístico

A implementação exige explicitamente:

- `product.kind = MEDICINE`;
- `product.anvisa_registration_status = REGISTERED`;
- `buyer.legal_nature` igual a `DIRECT_PUBLIC_ADMINISTRATION_BODY`, `AUTARCHY` ou
  `PUBLIC_FOUNDATION`;
- `operation.buyer_is_acquirer = YES`;
- data da operação dentro da vigência da versão.

Um valor conhecido incompatível produz `SEM_CLASSIFICACAO`. Ausência ou `UNKNOWN` em qualquer
fato necessário produz `NECESSITA_VALIDACAO` e relaciona o fato ausente. O motor não infere
natureza jurídica por CNPJ, nome, descrição ou NCM e não usa IA para a decisão.

O `DecisionTrace` registra regra/versão, condições avaliadas, valores esperados e observados,
dispositivo legal, catálogo, CST e cClassTrib. O motor da rota piloto foi identificado como
`0.6.0-rt-ibscbs-pilot`.

## 6. Ruleset piloto

| Campo | Valor |
|---|---|
| ID | `IBSCBS-PILOT-001` |
| versão | `1.0.0` |
| status | `PUBLISHED` |
| itens | somente `RT-IBSCBS-0003`, versão 1 |
| fingerprint | `aa701a24aaded859d52af421c9765721c867cb02720a39177feef4048af4295b` |

O ruleset deve ser informado explicitamente. Ele não é default global nem autoriza a execução das
outras cinco especificações.

## 7. Execuções validadas

| Cenário | Resultado | Evidência principal |
|---|---|---|
| positivo | `CONCLUSIVO` | CST `200`, cClassTrib `200010` |
| fato insuficiente | `NECESSITA_VALIDACAO` | `buyer.legal_nature` ausente |
| hipótese excluída | `SEM_CLASSIFICACAO` | adquirente `PUBLIC_COMPANY` |

A reprodução do caso positivo manteve o input hash
`60abea606480398b3f878df28476831b45eebb15dfd790ddb362324343ca5bdf`, o fingerprint do
ruleset, a regra/versão e o resultado `CONCLUSIVO`. A avaliação reproduzida referencia a avaliação
original por `reproduced_from_id`.

## 8. Interface

A página `/reforma-tributaria/consulta` identifica visivelmente **REGRA PILOTO REAL** e apresenta
a jornada `Produto → Consulta IBS/CBS → informações da operação → RT-IBSCBS-0003 →
CST/cClassTrib → fundamento legal → DecisionTrace → histórico reproduzível`. O produto cadastrado é
obrigatório; a tela coleta os quatro fatos governados, fixa o ruleset piloto e exibe snapshot do
produto, resultado, vigência, versão e hashes necessários à auditoria e reprodução.

## 9. Validações

- Ruff: aprovado;
- mypy estrito: aprovado;
- suíte Python: `109 passed`, `1 skipped` (teste PostgreSQL mutável opt-in; o estado real foi
  conferido por consulta somente leitura);
- testes do motor para RT-IBSCBS-0003: 15 casos, incluindo positivos, negativos, insuficiência e
  limites temporais;
- frontend: lint e typecheck aprovados; 4 arquivos/5 testes aprovados;
- PostgreSQL: regra e ruleset publicados, quatro execuções finais persistidas e nenhuma outra
  identidade tributária real encontrada.

## 10. Limitações deliberadas

- a plataforma não verifica automaticamente a autenticidade material da prova sanitária ou da
  natureza jurídica; recebe fatos governados e deixa dados ausentes visíveis;
- o ruleset é piloto, explícito e não é adotado como configuração produtiva global;
- nenhuma regra além de `RT-IBSCBS-0003` está executável;
- alterações jurídicas ou técnicas futuras exigem nova especificação/versão, sem sobrescrever o
  histórico publicado.


