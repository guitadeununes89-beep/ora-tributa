# Etapa 9.1 — matriz final de aprovação do primeiro bloco P1

- **Revalidação oficial:** 2026-09-03
- **Lifecycle das três especificações:** `DRAFT`
- **Catálogo vigente consultado:** 23/06/2026, IT 2025.002 v1.60
- **Catálogo governado:** `2295b90f-2f92-4fa4-8181-3007f02b1679`
- **Fingerprint:** `1448cb63b57d56c728da36ae7091ad2581b57fc8e364b2069c941c2009c654`

| Regra | cClassTrib | Status jurídico | Blocker | Próxima ação |
|---|---:|---|---|---|
| RT-IBSCBS-0007 v3 | 200022 | `READY_FOR_HUMAN_APPROVAL` | Nenhum bloqueador jurídico dentro do escopo nacional delimitado. A extensão regulamentar a certos bens estrangeiros está fora desta especificação e continua sem código inferido. | Submeter a v3 à aprovação humana; depois, e somente com nova autorização, avaliar implementação. |
| RT-IBSCBS-0008 v3 | 200023 | `READY_FOR_HUMAN_APPROVAL` | Nenhum bloqueador jurídico remanescente identificado. | Submeter a v3 à aprovação humana; depois, e somente com nova autorização, avaliar implementação. |
| RT-IBSCBS-0009 v3 | 200024 | `BLOCKED` | `BLOCKED_LEGAL_REFERENCE_CONFLICT`: catálogo cita habilitação pelo art. 456; LC 214/2025, art. 463, I, remete ao art. 460. | Aguardar retificação ou confirmação oficial inequívoca do catálogo; não aprovar. |

## Revalidação das fontes

As três especificações foram confrontadas com:

- LC nº 214/2025 compilada vigente, fonte governada
  `23302183-6c92-4b34-a26d-cd272e2c1b1e`;
- LC nº 227/2026, especialmente as alterações dos arts. 440, 442 e 460;
- Resolução CGIBS nº 6/2026, arts. 433, 435, 438, 516, 519, 527 e 551 a 553;
- Decreto nº 12.955/2026, na disciplina correspondente da CBS;
- catálogo oficial cClassTrib e IT 2025.002 v1.60, ainda apresentados como vigentes pelo Portal
  NF-e em 03/09/2026.

Vigência documental das três hipóteses: `effective_from = 2026-01-01` e `effective_to = null`, com
seleção temporal pela LC nº 214/2025, art. 544, VI. Uma futura alteração exige nova versão.

## Delimitação jurídica

### RT-IBSCBS-0007

- CST `200`; cClassTrib `200022`; fundamento central: art. 445;
- operação originada fora da ZFM, destinada à ZFM;
- bem material industrializado de origem nacional;
- adquirente contribuinte estabelecido na ZFM, habilitado pelo art. 442 e em regime admitido;
- exige território governado, inscrição Suframa, exclusão do art. 443 e prova de internamento/prazo;
- tratamento especial de alíquota zero precede futura regra geral somente quando todos os fatos
  estiverem confirmados e a relação de precedência estiver vinculada por ID.

A extensão do regulamento do IBS a certos bens estrangeiros não foi incorporada nem recebeu código
por analogia. Ela exige especificação separada e fonte oficial de mapeamento.

### RT-IBSCBS-0008

- CST `200`; cClassTrib `200023`; fundamento central: art. 448;
- operação entre indústrias incentivadas na ZFM;
- bem material intermediário e entrega/disponibilização dentro da área;
- exige qualificação oficial das duas indústrias, território governado, exclusões e escopo do valor
  adicionado em industrialização por encomenda;
- art. 450 afasta seu crédito presumido nas operações do art. 448;
- regra especial somente pretere futura regra geral com todos os fatos confirmados e vínculo por ID.

### RT-IBSCBS-0009

- CST `200`; cClassTrib `200024`; fundamento material identificado: art. 463;
- fatos materiais e territoriais permanecem documentados, mas não autorizam resultado conclusivo;
- a divergência `art. 456 × art. 460` não foi resolvida por fonte oficial;
- conclusão: `BLOCKED_LEGAL_REFERENCE_CONFLICT`.

## Testes jurídicos documentais

Cada especificação v3 contém pelo menos três positivos, três negativos, três inconclusivos, limites
temporal e territorial, fatos ausentes e um caso explícito de concorrência com tratamento geral. Na
0009, casos materialmente favoráveis continuam com `NECESSITA_VALIDACAO` enquanto o conflito existir.

## Pre-flight real

PostgreSQL local confirmado em escuta na porta 5432. O pre-flight foi executado após a versão v3:

| Regra | Schema | Fonte/catálogo | Blocker jurídico | Resultado do CLI |
|---|---|---|---|---|
| RT-IBSCBS-0007 v3 | válido | resolvidos | nenhum no escopo | `NOT_READY`: somente `STATUS_NOT_APPROVED` |
| RT-IBSCBS-0008 v3 | válido | resolvidos | nenhum | `NOT_READY`: somente `STATUS_NOT_APPROVED` |
| RT-IBSCBS-0009 v3 | válido | resolvidos | conflito 456 × 460 | `NOT_READY`: somente `STATUS_NOT_APPROVED`; o CLI não julga mérito jurídico |

Não houve erro estrutural, `SOURCE_NOT_FOUND`, `CATALOG_VERSION_NOT_FOUND` ou indisponibilidade do
lookup. Para 0007 e 0008 falta apenas o ato humano no plano documental; 0009 não pode receber esse
ato enquanto o conflito persistir.

## Cobertura

- executável atual: `1/164` (`0,61%`);
- potencial após futura aprovação, implementação testada e publicação apenas de 0007 e 0008:
  `3/164` (`1,83%`);
- potencial do lote completo, condicionado também à solução oficial e ao ciclo integral da 0009:
  `4/164` (`2,44%`).

Nenhum desses potenciais é cobertura atual.
