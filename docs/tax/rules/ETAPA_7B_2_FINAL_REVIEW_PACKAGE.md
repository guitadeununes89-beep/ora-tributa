# Pacote final de revisão — Etapa 7B.2

## Resultado executivo

- PostgreSQL local: **ativo**, versão 17.11, serviço `postgresql-x64-17`, em `localhost:5432`.
- Banco e papel técnicos: `tributaria`, conforme a configuração local documentada.
- Migrações: `alembic upgrade head` aplicou `0001` a `0005_products_assisted`; `alembic current`
  confirmou `0005_products_assisted (head)`.
- Inventário: zero organizações, fontes legais, catálogos, versões de catálogo, CSTs, cClassTrib,
  versões de regra e rulesets.
- Catálogo persistido: **ausente**; não existe snapshot `PUBLISHED` no banco.
- IDs governados resolvidos: **nenhum**.
- Marcadores substituídos: **nenhum**, pois não há IDs reais correspondentes.
- Preflight real: as seis especificações retornaram `NOT_READY` com
  `STATUS_NOT_APPROVED`, `SOURCE_NOT_FOUND` e `CATALOG_VERSION_NOT_FOUND`, exit code 1.
- Lifecycle: todas continuam `DRAFT`; nenhuma foi promovida.

## Referências e catálogo

### Confirmado pelo artefato oficial local

O arquivo `database/normative-artifacts/original/cClassTrib-2026-06-22.xlsx` continua íntegro e seu
SHA-256 calculado é
`1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654`, igual ao manifesto
`ibscbs-cclasstrib-2026-06-23.json`. O manifesto também registra:

- hash normalizado: `9b65c977cdd37b30f0146b10f8addd7175f11389fc08196a9dfebfd5258b2008`;
- assinatura do schema: `fb87c22952135fe428a552f32d330d2cdd132bd5aae6dfc0a33747c58a6135c6`;
- 18 CSTs e 164 cClassTrib;
- publicação oficial em 23/06/2026.

As correspondências documentais já verificadas na Etapa 7B.1 permanecem:

| Regra | CST | cClassTrib | Correspondência documental |
|---|---:|---:|---|
| RT-IBSCBS-0001 | 200 | 200032 | Medicamentos registrados na Anvisa ou produzidos por farmácia de manipulação, ressalvada alíquota zero; art. 133 |
| RT-IBSCBS-0002 | 200 | 200009 | Medicamentos registrados na Anvisa; art. 146 atual |
| RT-IBSCBS-0003 | 200 | 200010 | Aquisição por administração pública ou entidade imune; art. 146, § 1º, I e II |
| RT-IBSCBS-0004 | 200 | 200009 | Medicamentos do Anexo XIV; art. 146 original, no catálogo histórico de 15/12/2025 |
| RT-IBSCBS-0005 | 200 | 200010 | Aquisição por administração pública ou entidade imune; art. 146, § 1º, I e II |
| RT-IBSCBS-0006 | 200 | 200053 | Soros e vacinas; art. 146, § 1º, III |

### Confirmado no PostgreSQL

A consulta real confirmou que não existem `legal_source_id`, `catalog_version_id`, tenant,
snapshot `PUBLISHED`, hash persistido, contagens ou linhas CST/cClassTrib no banco. O artefato no
Git não prova publicação no PostgreSQL e não foi ingerido automaticamente. Conforme o gate da
etapa, a ausência interrompe a resolução e preserva os marcadores:

- `PENDING-LC214-2025-COMPILED`;
- `PENDING-LC214-2025-ORIGINAL`;
- `PENDING-PUBLISHED-CATALOG-1448CB63A41B`;
- `PENDING-GOVERNED-CATALOG-2025-12-15`.

## Equivalência de prontidão

O comando existente só possui `READY_FOR_IMPLEMENTATION` e `NOT_READY`. Ele exige status
`APPROVED`, de modo que não representa o gate intermediário solicitado. Nenhum lifecycle ou contrato
foi alterado sem ADR.

Neste pacote, `READY_FOR_LEGAL_APPROVAL` seria apenas uma avaliação documental derivada: documento
estruturalmente válido, referências governadas resolvidas e ausência de pesquisa normativa
pendente. Não é um novo estado do sistema e não autoriza implementação. Como as referências foram
consultadas e estão ausentes, todas as regras permanecem `NOT_READY` nesta execução.

## Preflight real

Comando executado para cada arquivo:

```powershell
.\.venv\Scripts\python.exe -m tributaria_api.tax_rule_spec_cli `
  docs\tax\rules\specifications\RT-IBSCBS-000N.json `
  --organization-id dev-org
```

| Rule ID | Versão | Status documental | Resultado | Issues | Exit |
|---|---:|---|---|---|---:|
| RT-IBSCBS-0001 | 2 | DRAFT | NOT_READY | STATUS_NOT_APPROVED; SOURCE_NOT_FOUND; CATALOG_VERSION_NOT_FOUND | 1 |
| RT-IBSCBS-0002 | 2 | DRAFT | NOT_READY | STATUS_NOT_APPROVED; SOURCE_NOT_FOUND; CATALOG_VERSION_NOT_FOUND | 1 |
| RT-IBSCBS-0003 | 2 | DRAFT | NOT_READY | STATUS_NOT_APPROVED; SOURCE_NOT_FOUND; CATALOG_VERSION_NOT_FOUND | 1 |
| RT-IBSCBS-0004 | 1 | DRAFT | NOT_READY | STATUS_NOT_APPROVED; SOURCE_NOT_FOUND; CATALOG_VERSION_NOT_FOUND | 1 |
| RT-IBSCBS-0005 | 1 | DRAFT | NOT_READY | STATUS_NOT_APPROVED; SOURCE_NOT_FOUND; CATALOG_VERSION_NOT_FOUND | 1 |
| RT-IBSCBS-0006 | 1 | DRAFT | NOT_READY | STATUS_NOT_APPROVED; SOURCE_NOT_FOUND; CATALOG_VERSION_NOT_FOUND | 1 |

## RT-IBSCBS-0001 — classe B

- **Título:** Fornecimento de medicamento registrado na Anvisa com redução de 60% das alíquotas do
  IBS e da CBS.
- **Fundamento/dispositivo:** LC nº 214/2025, arts. 128, V, 133, caput e §§ 1º–2º, 146 e 544, VI;
  LC nº 227/2026, arts. 174 e 182, III.
- **Vigência/cobertura temporal:** desde 01/01/2026; a precedência exige avaliar antes todas as
  hipóteses temporalmente aplicáveis do art. 146.
- **CST/cClassTrib:** 200 / 200032.
- **IDs governados:** `legal_source_id=PENDING-LC214-2025-COMPILED`;
  `catalog_version_id=PENDING-PUBLISHED-CATALOG-1448CB63A41B`.
- **Fatos obrigatórios:** data; natureza e registro Anvisa do produto; forma de fornecimento;
  identidades de fornecedor, fabricante e importador; papel e validação da entidade do § 2º;
  condição de preço; cobertura e resultado agregado do art. 146.
- **Precedência:** regras de alíquota zero do art. 146 precedem esta hipótese.
- **Exemplos de teste:** POS-001/POS-002; NEG-001/NEG-002; INC-001/INC-002; DATE-001/DATE-002.
- **Bloqueadores restantes:** entidade responsável pelo art. 133, § 2º; suficiência probatória;
  cobertura integral das hipóteses de alíquota zero; referências governadas.
- **Revisão humana:** confirmar a pessoa jurídica relevante e a prova aceitável sem presumir a
  identidade do fornecedor.

## RT-IBSCBS-0002 — classe C

- **Título:** Fornecimento de medicamento registrado na Anvisa com alíquota zero por destinação
  sanitária legal.
- **Fundamento/dispositivo:** LC nº 214/2025, art. 146, caput, I–VII e §§ 3º–4º; art. 133; LC nº
  227/2026, arts. 174 e 182, III.
- **Vigência/cobertura temporal:** desde 14/01/2026; não cobre a redação histórica.
- **CST/cClassTrib:** 200 / 200009.
- **IDs governados:** `legal_source_id=PENDING-LC214-2025-COMPILED`;
  `catalog_version_id=PENDING-PUBLISHED-CATALOG-1448CB63A41B`.
- **Fatos obrigatórios:** data; natureza e registro Anvisa; destinação sanitária; correspondência ao
  registro sanitário; presença na lista temporal do § 3º.
- **Precedência:** precede RT-IBSCBS-0001.
- **Exemplos de teste:** POS-001/POS-002; NEG-001/NEG-002; INC-001/INC-002; DATE-001/DATE-002.
- **Bloqueadores restantes:** lista oficial do art. 146, § 3º; função jurídica da lista;
  vocabulário canônico das destinações; referências governadas.
- **Revisão humana:** não remover `LISTED` nem inferir conteúdo da lista sem ato oficial.

## RT-IBSCBS-0003 — classe A condicionada

- **Título:** Fornecimento de medicamento registrado na Anvisa adquirido pela administração pública
  direta, autarquia ou fundação pública com alíquota zero.
- **Fundamento/dispositivo:** LC nº 214/2025, art. 146, § 1º, I; arts. 133 e 544, VI; LC nº 227/2026,
  arts. 174 e 182, III.
- **Vigência/cobertura temporal:** desde 01/01/2026, preservando a redação original e a redação
  reestruturada desde 14/01/2026.
- **CST/cClassTrib:** 200 / 200010.
- **IDs governados:** `legal_source_id=PENDING-LC214-2025-COMPILED`;
  `catalog_version_id=PENDING-PUBLISHED-CATALOG-1448CB63A41B`.
- **Fatos obrigatórios:** data; natureza e registro Anvisa; natureza jurídica do comprador; prova de
  que ele é o adquirente efetivo.
- **Precedência:** precede RT-IBSCBS-0001.
- **Exemplos de teste:** POS-001/POS-002; NEG-001/NEG-002; INC-001/INC-002; DATE-001/DATE-002.
- **Bloqueadores restantes:** referências governadas; metadados de revisão e aprovação; confirmação
  humana de que a cClassTrib compartilhada 200010 não amplia o recorte do inciso I.
- **Revisão humana:** é a única candidata A, mas não está pronta agora porque os IDs não puderam ser
  verificados.

## RT-IBSCBS-0004 — classe B

- **Título:** Fornecimento de medicamentos relacionados no Anexo XIV da redação original da LC nº
  214/2025.
- **Fundamento/dispositivo:** LC nº 214/2025, art. 146, caput original, Anexo XIV e art. 544, VI; LC
  nº 227/2026, arts. 174 e 182, III.
- **Vigência/cobertura temporal:** `[2026-01-01, 2026-01-14)`, último dia material em 13/01/2026.
- **CST/cClassTrib:** 200 / 200009.
- **IDs governados:** `legal_source_id=PENDING-LC214-2025-ORIGINAL`;
  `catalog_version_id=PENDING-GOVERNED-CATALOG-2025-12-15`.
- **Fatos obrigatórios:** data; NCM/SH; correspondência ao Anexo XIV; versão normativa do anexo.
- **Precedência:** precede RT-IBSCBS-0001 no intervalo histórico.
- **Exemplos de teste:** POS-001/POS-002; NEG-001/NEG-002; INC-001/INC-002; DATE-001/DATE-002.
- **Bloqueadores restantes:** fonte original e catálogo histórico governados; conferência individual
  e temporal do Anexo XIV; metadados de aprovação.
- **Revisão humana:** confirmar a correspondência histórica sem reutilizar o catálogo atual.

## RT-IBSCBS-0005 — classe B

- **Título:** Medicamento registrado na Anvisa adquirido por entidade de saúde imune com CEBAS e
  prestação de serviços ao SUS.
- **Fundamento/dispositivo:** LC nº 214/2025, art. 146, § 1º, II; LC nº 187/2021, arts. 9º–11; art.
  544, VI; LC nº 227/2026, arts. 174 e 182, III.
- **Vigência/cobertura temporal:** desde 01/01/2026.
- **CST/cClassTrib:** 200 / 200010.
- **IDs governados:** `legal_source_id=PENDING-LC214-2025-COMPILED`;
  `catalog_version_id=PENDING-PUBLISHED-CATALOG-1448CB63A41B`; referência governada específica à LC
  nº 187/2021 ainda não está representada no documento.
- **Fatos obrigatórios:** data; natureza e registro Anvisa; natureza da entidade de saúde; imunidade;
  CEBAS; requisito SUS; adquirente efetivo.
- **Precedência:** precede RT-IBSCBS-0001.
- **Exemplos de teste:** POS-001/POS-002; NEG-001/NEG-002; INC-001/INC-002; DATE-001/DATE-002.
- **Bloqueadores restantes:** requisitos específicos do § 1º, II; suficiência das evidências de
  imunidade, CEBAS, SUS e adquirente efetivo; referências governadas.
- **Revisão humana:** manter DecisionTrace separada da RT-IBSCBS-0003, apesar da cClassTrib comum.

## RT-IBSCBS-0006 — classe C

- **Título:** Medicamento registrado na Anvisa classificado como soro ou vacina conforme
  regulamentação sanitária específica.
- **Fundamento/dispositivo:** LC nº 214/2025, art. 146, § 1º, III e § 3º; LC nº 227/2026, arts. 174 e
  182, III.
- **Vigência/cobertura temporal:** desde 14/01/2026.
- **CST/cClassTrib:** 200 / 200053.
- **IDs governados:** `legal_source_id=PENDING-LC214-2025-COMPILED`;
  `catalog_version_id=PENDING-PUBLISHED-CATALOG-1448CB63A41B`.
- **Fatos obrigatórios:** data; natureza e registro Anvisa; classificação como soro/vacina;
  regulamentação sanitária específica; lista temporal do § 3º.
- **Precedência:** precede RT-IBSCBS-0001.
- **Exemplos de teste:** POS-001/POS-002; NEG-001/NEG-002; INC-001/INC-002; DATE-001/DATE-002.
- **Bloqueadores restantes:** regulamentação sanitária oficial aplicável; lista oficial do § 3º;
  referências governadas.
- **Revisão humana:** não transformar atributos sanitários ou descrição comercial em enquadramento.

## Lista de submissão e pesquisa

- **Prontas agora para aprovação jurídica humana final:** nenhuma, porque as referências governadas
  não puderam ser verificadas.
- **Candidata A após resolução técnica dos IDs:** `RT-IBSCBS-0003`.
- **Exigem confirmação normativa adicional:** `RT-IBSCBS-0001`, `RT-IBSCBS-0004` e
  `RT-IBSCBS-0005`.
- **Exigem nova fonte ou regulamentação oficial:** `RT-IBSCBS-0002` e `RT-IBSCBS-0006`.

## Confirmação de não implementação

Nenhuma `TaxRuleVersion` real foi criada. Nenhum ruleset tributário real foi publicado. Nenhuma das
seis especificações está executável pelo `tax-engine`, e seu comportamento produtivo não foi
alterado.
