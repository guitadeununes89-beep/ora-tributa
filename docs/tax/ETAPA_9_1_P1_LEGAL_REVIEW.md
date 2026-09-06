# Etapa 9.1 — revisão e saneamento jurídico do primeiro lote P1

> **Fechamento posterior — 2026-09-03:** este documento preserva o diagnóstico inicial da revisão.
> A matriz final `ETAPA_9_1_FINAL_APPROVAL_MATRIX.md` o sucede sem apagar o histórico: as versões v3
> de 0007 e 0008 estão `READY_FOR_HUMAN_APPROVAL`; 0009 permanece `BLOCKED`. Todas continuam DRAFT.

## Resultado executivo da revisão inicial — registro histórico

As três especificações foram revalidadas exclusivamente contra fontes oficiais e continuam
`DRAFT`. Não houve TaxRuleVersion, ruleset ou mudança no tax-engine. A cobertura executável segue
`1/164` (`0,61%`).

| Regra | CST | cClassTrib | Resultado | Situação |
|---|---:|---:|---|---|
| RT-IBSCBS-0007 v2 | 200 | 200022 | B — `NEEDS_LEGAL_ADJUSTMENT` | bloqueada para aprovação |
| RT-IBSCBS-0008 v2 | 200 | 200023 | A — `READY_FOR_HUMAN_APPROVAL` | pode ser submetida à revisão final |
| RT-IBSCBS-0009 v2 | 200 | 200024 | C — `BLOCKED_EXTERNAL_OR_LEGAL_SOURCE` | `BLOCKED_LEGAL_REFERENCE_CONFLICT` |

## Fontes, versões e temporalidade

- LC nº 214/2025 compilada, fonte governada `23302183-6c92-4b34-a26d-cd272e2c1b1e`,
  SHA-256 `aacfd146f2c91291c3c8675035da70cb08b359bca03b3ccc21c5b3a14e6a7719`;
- LC nº 227/2026, que altera as definições e habilitações dos arts. 440, 442 e 460;
- Resolução CGIBS nº 6/2026, especialmente arts. 433, 435, 438, 516, 519, 527 e 551 a 553;
- Decreto nº 12.955/2026, regulamento da CBS com estrutura material correspondente;
- tabela cClassTrib publicada em 23/06/2026, ID
  `2295b90f-2f92-4fa4-8181-3007f02b1679`, fingerprint
  `1448cb63b57d56c728da36ae7091ad2581b57fc8e364b2069c941c2009c654`;
- IT 2025.002 v1.60.

Para as três hipóteses, `effective_from = 2026-01-01`, `effective_to = null`. O art. 544, VI,
alcança as disposições que não receberam data especial. Não foi identificada mudança de numeração dos
arts. 445, 448 ou 463 pela LC nº 227/2026.

## RT-IBSCBS-0007

- **status jurídico:** B — `NEEDS_LEGAL_ADJUSTMENT`;
- **CST:** 200;
- **cClassTrib:** 200022;
- **fundamento:** arts. 440, 442, 443, § 1º, 445 e 544, VI;
- **tratamento e precedência:** alíquota zero expressa; a futura regra geral somente será preterida por
  ID quando existir e todos os fatos especiais estiverem confirmados;
- **fatos:** data; versão territorial ZFM; origem fora; destino e estabelecimento na ZFM; bem material,
  industrializado e de origem nacional; adquirente contribuinte; habilitação art. 442; regime regular ou
  Simples; exclusão art. 443; inscrição Suframa no documento; evento de internamento; prazo de 120 dias
  ou prorrogação válida até 210 dias; industrialização por encomenda quando aplicável;
- **bloqueadores:** o regulamento do IBS estende a hipótese a certos bens estrangeiros, mas a descrição
  de 200022 registra origem nacional; falta confirmação oficial do mapeamento desse escopo adicional.
  O cadastro territorial e atos operacionais conjuntos ainda precisam de ingestão governada.

Os casos cobrem três positivos documentais, três negativos, três inconclusivos, 31/12/2025,
01/01/2026, pendência dentro do prazo e insuficiência de CEP/município.

## RT-IBSCBS-0008

- **status jurídico:** A — `READY_FOR_HUMAN_APPROVAL`;
- **CST:** 200;
- **cClassTrib:** 200023;
- **fundamento:** arts. 440, II e III, 442, II, 443, § 1º, 448 e 544, VI;
- **tratamento e precedência:** alíquota zero expressa; na industrialização por encomenda, somente o
  valor adicionado; o art. 450 exclui as operações do art. 448 de seu crédito presumido;
- **fatos:** data; versão territorial; estabelecimentos do fornecedor e adquirente na ZFM; qualificação
  de ambos como indústrias incentivadas; bem material intermediário conforme definição legal; entrega
  ou disponibilização dentro da área; exclusão art. 443; tipo de fluxo e escopo do valor adicionado;
- **bloqueadores:** nenhum bloqueador jurídico remanescente. O cadastro territorial é dependência de
  implementação futura e não autoriza uso de CEP/UF isolados.

Os casos cobrem consumo produtivo, embalagem, encomenda, três negativas, três inconclusivas,
limites temporais, fronteira territorial e conflito com tratamento geral.

## RT-IBSCBS-0009

- **status jurídico:** C — `BLOCKED_EXTERNAL_OR_LEGAL_SOURCE`;
- **CST:** 200 no catálogo;
- **cClassTrib:** 200024 no catálogo;
- **fundamento legal identificado:** arts. 459, 460, 461, § 1º, 463 e 544, VI;
- **conflito identificado:** a descrição oficial de 200024 cita habilitação pelo art. 456; a redação
  original e compilada do art. 463 remete ao art. 460; a LC nº 227/2026 altera o art. 460 sem mudar a
  remissão; a Resolução CGIBS nº 6/2026 usa o art. 438, contraparte do art. 460;
- **conclusão:** `BLOCKED_LEGAL_REFERENCE_CONFLICT`. Cenários materialmente favoráveis continuam
  `NECESSITA_VALIDACAO` e não retornam CST/cClassTrib enquanto não houver ato oficial corretivo ou
  confirmatório.

O relatório específico é `docs/tax/rules/RT-IBSCBS-0009_LEGAL_DISCREPANCY_REPORT.md`.

## Territorialidade

O ADR-0021 aprovou conceitualmente `TaxJurisdictionArea`: referência territorial oficial,
versionada e imutável. UF, município textual e CEP são apenas indícios. Nenhuma lista municipal foi
inserida no Python e nenhuma estrutura persistente foi implementada nesta etapa.

## Dashboard e pipeline

O ADR-0022 separa `review_readiness` do lifecycle. A cobertura passa a exibir catálogo, mapeamento,
DRAFT, pronto para revisão, bloqueado, aprovado e publicado. DRAFT não conta como cobertura
executável. O fluxo reutilizável está em `docs/tax/rules/FAMILY_LEGAL_REVIEW_PIPELINE.md`.

## Preflight real

O comando `validate-tax-rule-spec` foi executado contra `dev-governance-org` e o PostgreSQL local
em escuta na porta 5432:

| Regra | Schema | Fonte/catálogo governados | Resultado técnico |
|---|---|---|---|
| RT-IBSCBS-0007 v2 | válido | resolvidos | `NOT_READY`: somente `STATUS_NOT_APPROVED` |
| RT-IBSCBS-0008 v2 | válido | resolvidos | `NOT_READY`: somente `STATUS_NOT_APPROVED` |
| RT-IBSCBS-0009 v2 | válido | resolvidos | `NOT_READY`: somente `STATUS_NOT_APPROVED` |

O CLI atual usa `READY_FOR_IMPLEMENTATION`, não um estado intermediário. Conforme ADR-0022, a
prontidão para revisão humana é uma projeção separada: somente 0008 está
`READY_FOR_HUMAN_REVIEW`. O preflight estrutural não sana nem julga o conflito de 0009.

## Fontes oficiais consultadas

- https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm
- https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm
- https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm
- https://www.cgibs.gov.br/regulamentos
- https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf
- https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=/NJarYc9nus=
- https://www.gov.br/suframa/pt-br/sistemas/simnac/sobre

## Gate final

Somente RT-IBSCBS-0008 está pronta para nova aprovação humana. RT-IBSCBS-0007 requer ajuste jurídico
do escopo/catalogação e RT-IBSCBS-0009 requer fonte oficial que resolva o conflito. Nenhuma das três
foi implementada ou publicada.
