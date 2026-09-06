# Etapa 9 — seleção do primeiro bloco P1 de cobertura nacional

## Escopo e fontes governadas

Esta seleção usa exclusivamente:

- `IBSCBS_NATIONAL_COVERAGE_MATRIX.md`, derivada do catálogo oficial `2026-06-23`, ID
  `2295b90f-2f92-4fa4-8181-3007f02b1679`, em estado `PUBLISHED`;
- `IBSCBS_COVERAGE_ROADMAP.md`, no qual P1 corresponde à família oficial `Padrão`;
- Lei Complementar nº 214/2025, texto compilado oficial, fonte governada
  `23302183-6c92-4b34-a26d-cd272e2c1b1e`, SHA-256
  `aacfd146f2c91291c3c8675035da70cb08b359bca03b3ccc21c5b3a14e6a7719`.

Catálogo, descrição e indicadores não são regras. A comparação não autoriza implementação.

## Comparação das principais subfamílias P1

| Subfamília candidata | cClassTrib considerados | Quantidade | Base principal | Dependência externa | Determinismo documental | Decisão |
|---|---|---:|---|---|---|---|
| Operações com bens na ZFM e ALC | `200022`, `200023`, `200024` | 3 | arts. 445, 448 e 463 | média: habilitação Suframa, qualificação industrial, ingresso e território | alta após prova oficial dos fatos | **selecionada** |
| Transportes com regime ou destino específico | `200001`, `200021`, `200049`, `200050`, `222001` | 5 | arts. 103, 285, 286, 287 e 12, § 8º | média/alta: modalidade, trecho, concessão e documentos setoriais | média; dispositivos heterogêneos | adiada |
| Operações com imóveis | `200026`, `200027`, `200045`, `200046` | 4 | arts. 158 e 261 | alta: objeto imóvel, ato municipal/distrital e marcos temporais | média | adiada; exige evolução de domínio |
| Bens vinculados a anexos e NCM/SH | exemplos `200003`, `200013`, `200014` | 3 no recorte | arts. 125, 147 e 148 e anexos aplicáveis | alta: ingestão temporal de anexos e classificação oficial | média após catálogo complementar | adiada |
| Regime automotivo incentivado | `000003`, `000004` | 2 | arts. 311 e 312 | alta: projeto incentivado e atos habilitadores | média | adiada por menor volume e dependências |

As cinco classificações de transporte não formam uma única regra: a quantidade é atraente, mas os
dispositivos e fatos variam entre ZPE, transporte urbano/metropolitano, intermunicipal/interestadual,
aéreo regional e venda conjunta internacional. Agrupá-los numa regra seria artificial.

## Família selecionada

**Operações com bens na Zona Franca de Manaus e em Áreas de Livre Comércio**, dentro da família
oficial P1 `Padrão`.

Motivos:

1. não é centrada em medicamentos;
2. cobre três cClassTrib com fatos operacionais reutilizáveis;
3. os caputs e exclusões possuem recorte objetivo na LC nº 214/2025;
4. trata de bens materiais e não exige ampliar `Product` para serviço, direito ou imóvel;
5. dependências externas podem ser representadas como evidência obrigatória e bloqueador, sem
   inferência do sistema;
6. cada hipótese permanece em especificação separada, permitindo múltiplas regras futuras para o
   mesmo código quando a revisão jurídica identificar subdivisões necessárias.

## Especificações criadas

| Rule ID | CST | cClassTrib | Dispositivo | Status | Implementação |
|---|---:|---:|---|---|---|
| `RT-IBSCBS-0007` | 200 | 200022 | arts. 442 e 445 | `DRAFT` | nenhuma |
| `RT-IBSCBS-0008` | 200 | 200023 | art. 448 | `DRAFT` | nenhuma |
| `RT-IBSCBS-0009` | 200 | 200024 | arts. 459, 460 e 463 | `DRAFT` | nenhuma |

## Preflight real

O comando `validate-tax-rule-spec`, executado contra `dev-governance-org`, confirmou fonte,
catálogo `PUBLISHED`, CST, cClassTrib, vigência estrutural, fatos e casos de teste para os três
documentos. O resultado deliberado foi:

| Rule ID | Readiness | Issue |
|---|---|---|
| `RT-IBSCBS-0007` | `NOT_READY` | `STATUS_NOT_APPROVED` |
| `RT-IBSCBS-0008` | `NOT_READY` | `STATUS_NOT_APPROVED` |
| `RT-IBSCBS-0009` | `NOT_READY` | `STATUS_NOT_APPROVED` |

Não ocorreram `SOURCE_NOT_FOUND`, `CATALOG_VERSION_NOT_FOUND` ou falhas de schema. O preflight é
estrutural e não atesta mérito jurídico.

## Bloqueadores jurídicos e probatórios

### RT-IBSCBS-0007

- regulamentação oficial dos controles e prazo de ingresso dos §§ 3º e 4º do art. 445;
- fonte, validade temporal e suficiência da prova de habilitação pelo art. 442;
- confirmação humana da produção de efeitos no período de transição.

### RT-IBSCBS-0008

- padrão oficial de prova da condição de indústria incentivada para as duas partes;
- padrão probatório da natureza de bem intermediário no projeto produtivo;
- confirmação humana da produção de efeitos no período de transição.

### RT-IBSCBS-0009

- divergência a resolver por fonte/revisão humana: a descrição do catálogo para `200024` menciona
  art. 456, enquanto o art. 463, I, do texto compilado remete ao art. 460;
- regulamentação oficial de habilitação e ingresso nas ALC;
- fonte governada da identidade e limites territoriais da ALC;
- confirmação humana da produção de efeitos no período de transição.

Nenhuma lacuna acima foi preenchida por memória, descrição comercial ou inferência.

## Efeito potencial sobre cobertura

- antes da Etapa 9: `1/164` cClassTrib executável, ou `0,61%`;
- após esta etapa: a cobertura executável continua `1/164` (`0,61%`), porque os três documentos são
  `DRAFT`;
- após eventual aprovação jurídica, isoladamente: a cobertura executável ainda será `1/164`, pois
  aprovação não equivale a implementação ou publicação;
- teto potencial, somente após aprovação, implementação testada e publicação futura das três
  hipóteses: `4/164`, ou `2,44%`.

O percentual potencial é cenário condicional de planejamento, não cobertura existente.

## Gate obrigatório seguinte

`DRAFT → revisão jurídica humana → APPROVED → implementação testada → TaxRuleVersion PUBLISHED →
ruleset explícito`.

Esta etapa não criou TaxRuleVersion, não publicou ruleset e não alterou o tax-engine.

## Atualização da Etapa 9.1

O lote passou pelo pipeline reutilizável documentado em
`docs/tax/rules/FAMILY_LEGAL_REVIEW_PIPELINE.md`. Resultado:

- RT-IBSCBS-0007: B — `NEEDS_LEGAL_ADJUSTMENT`;
- RT-IBSCBS-0008: A — `READY_FOR_HUMAN_APPROVAL`;
- RT-IBSCBS-0009: C — `BLOCKED_EXTERNAL_OR_LEGAL_SOURCE`.

As três especificações permanecem `DRAFT`; a cobertura executável continua `1/164` (`0,61%`).
