# Relatório de validação das regras piloto — Etapa 7B

## Estado do relatório

- **Data da consolidação:** 2026-08-30
- **Escopo:** fechamento documental da Etapa 7B
- **Lifecycle das três especificações:** `DRAFT`
- **Autorização para implementação:** nenhuma
- **Regra brasileira real executável:** nenhuma

Este relatório consolida os documentos existentes sem alterar interpretação jurídica. As fontes,
condições, vigências e códigos abaixo reproduzem as especificações da Etapa 7B e ainda dependem da
revisão humana indicada em cada seção.

## RT-IBSCBS-0001

### Identificação

| Campo | Valor |
|---|---|
| `rule_id` | `RT-IBSCBS-0001` |
| Título | Fornecimento de medicamento registrado na Anvisa com redução de 60% das alíquotas do IBS e da CBS |
| Status | `DRAFT` |
| Fundamento legal | Lei Complementar nº 214/2025 |
| Dispositivo | Arts. 128, V, 133, caput e §§ 1º e 2º, 146 e 544, VI; LC nº 227/2026, arts. 174 e 182, III |
| Fonte oficial | [LC nº 214/2025 — texto vigente, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html) |
| Vigência documentada | 01/01/2026, com seleção temporal da redação aplicável do art. 146 |
| CST | `200` |
| cClassTrib | `200032` |
| Preflight local | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |

### CONFIRMADO PELA FONTE OFICIAL

- o art. 133 prevê redução de 60% para o fornecimento abrangido pelo dispositivo;
- medicamentos sujeitos à alíquota zero do art. 146 são expressamente ressalvados;
- o § 2º contém condição relacionada ao compromisso de ajustamento ou à sistemática CMED para
  medicamentos industrializados ou importados;
- a regra documentada produz efeitos desde 01/01/2026;
- CST `200` e cClassTrib `200032` foram encontrados no catálogo oficial versionado, vinculados ao
  art. 133.

### Fatos obrigatórios

- data da operação;
- confirmação de que o produto é medicamento;
- situação temporal do registro Anvisa;
- forma de fornecimento: industrializado ou importado no escopo deste DRAFT;
- condição do fornecedor perante compromisso de ajustamento ou sistemática CMED;
- resultado temporal da avaliação de todas as hipóteses aplicáveis do art. 146.

### Exceções e exclusões

- qualquer hipótese de alíquota zero do art. 146;
- ausência de confirmação do registro Anvisa;
- falta da condição do art. 133, § 2º;
- medicamentos de manipulação e composições do § 1º, que exigem especificações próprias.

### Casos documentados

- positivos: 2;
- negativos: 2;
- inconclusivos: 2, ambos com `NECESSITA_VALIDACAO`;
- limites temporais: 2.

### PRECISA DE VALIDAÇÃO HUMANA

- suficiência das evidências de compromisso de ajustamento ou cumprimento da sistemática CMED;
- vínculo do identificador persistido da fonte oficial;
- vínculo do ID governado do snapshot `PUBLISHED` do catálogo;
- completude das especificações de alíquota zero usadas para excluir o art. 133;
- autoria, revisão e aprovação jurídica.

## RT-IBSCBS-0002

### Identificação

| Campo | Valor |
|---|---|
| `rule_id` | `RT-IBSCBS-0002` |
| Título | Fornecimento de medicamento registrado na Anvisa com alíquota zero por destinação sanitária legal |
| Status | `DRAFT` |
| Fundamento legal | Lei Complementar nº 214/2025, redação da LC nº 227/2026 |
| Dispositivo | Art. 146, caput, incisos I a VII e §§ 3º e 4º; art. 133, caput; LC nº 227/2026, arts. 174 e 182, III |
| Fonte oficial | [LC nº 214/2025 — texto vigente, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html) e [LC nº 227/2026, Planalto](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm) |
| Vigência documentada | 14/01/2026 |
| CST | `200` |
| cClassTrib | `200009` |
| Preflight local | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |

### CONFIRMADO PELA FONTE OFICIAL

- o caput exige medicamento registrado na Anvisa e destinação de acordo com o registro sanitário;
- os incisos enumeram doenças raras, doenças negligenciadas, oncologia, diabetes, HIV/aids e outras
  IST, doenças cardiovasculares e Programa Farmácia Popular do Brasil ou equivalente;
- o § 3º prevê divulgação periódica de lista por ato conjunto;
- a redação usada produz efeitos desde a publicação da LC nº 227/2026 em 14/01/2026;
- CST `200` e cClassTrib `200009` foram encontrados no catálogo oficial versionado, vinculados ao
  art. 146.

### Fatos obrigatórios

- data da operação;
- confirmação de que o produto é medicamento;
- situação temporal do registro Anvisa;
- destinação sanitária dentre as hipóteses legais;
- correspondência entre a destinação e o registro sanitário;
- situação do medicamento na lista temporal do art. 146, § 3º.

### Exceções e exclusões

- produto não registrado na Anvisa;
- finalidade fora dos incisos I a VII;
- finalidade incompatível com o registro sanitário;
- hipóteses autônomas do § 1º;
- atos temporários de emergência do § 4º, que exigem especificação própria.

### Casos documentados

- positivos: 2;
- negativos: 2;
- inconclusivos: 2, ambos com `NECESSITA_VALIDACAO`;
- limites temporais: 2.

### PRECISA DE VALIDAÇÃO HUMANA

- natureza jurídica da lista do § 3º: requisito constitutivo ou instrumento de divulgação;
- identificação e versionamento do ato conjunto temporalmente aplicável;
- vocabulário canônico das destinações sanitárias;
- vínculo do identificador persistido da fonte e do snapshot `PUBLISHED`;
- autoria, revisão e aprovação jurídica.

## RT-IBSCBS-0003

### Identificação

| Campo | Valor |
|---|---|
| `rule_id` | `RT-IBSCBS-0003` |
| Título | Fornecimento de medicamento registrado na Anvisa adquirido pela administração pública direta, autarquia ou fundação pública com alíquota zero |
| Status | `DRAFT` |
| Fundamento legal | Lei Complementar nº 214/2025 |
| Dispositivo | Art. 146, § 1º, I; art. 133, caput; art. 544, VI; LC nº 227/2026, arts. 174 e 182, III |
| Fonte oficial | [LC nº 214/2025 — texto vigente](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html) e [publicação original](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-publicacaooriginal-174141-pl.html) |
| Vigência documentada | 01/01/2026; hipótese mantida pela LC nº 227/2026 desde 14/01/2026 |
| CST | `200` |
| cClassTrib | `200010` |
| Preflight local | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` |

### CONFIRMADO PELA FONTE OFICIAL

- a hipótese exige medicamento registrado na Anvisa;
- os adquirentes enumerados são órgãos da administração pública direta, autarquias e fundações
  públicas;
- a hipótese já constava da redação original eficaz em 01/01/2026 e foi mantida na redação da LC
  nº 227/2026;
- CST `200` e cClassTrib `200010` foram encontrados no catálogo oficial versionado, relacionado ao
  fornecimento de medicamentos adquiridos por órgãos da administração pública.

### Fatos obrigatórios

- data da operação;
- confirmação de que o produto é medicamento;
- situação temporal do registro Anvisa;
- natureza jurídica comprovada do adquirente;
- confirmação de que o ente qualificado é o adquirente efetivo da operação.

### Exceções e exclusões

- produto não registrado na Anvisa;
- adquirente fora das três categorias do inciso I;
- enquadramento presumido somente por CNPJ ou nome;
- empresa pública, sociedade de economia mista ou entidade privada por mera aparência pública;
- entidades imunes com CEBAS do inciso II, fora do escopo deste DRAFT.

### Casos documentados

- positivos: 2;
- negativos: 2;
- inconclusivos: 2, ambos com `NECESSITA_VALIDACAO`;
- limites temporais: 2.

### PRECISA DE VALIDAÇÃO HUMANA

- adequação da cClassTrib `200010` ao recorte exclusivo do inciso I, pois a descrição oficial também
  menciona entidades imunes do inciso II;
- fontes probatórias admitidas para natureza jurídica e adquirente efetivo;
- vocabulário canônico das naturezas jurídicas;
- vínculo do identificador persistido da fonte e do snapshot `PUBLISHED`;
- autoria, revisão e aprovação jurídica.

## Resultado consolidado do preflight

| Regra | Resultado real do comando | Validação estrutural controlada |
|---|---|---|
| RT-IBSCBS-0001 | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` | `NOT_READY — STATUS_NOT_APPROVED` |
| RT-IBSCBS-0002 | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` | `NOT_READY — STATUS_NOT_APPROVED` |
| RT-IBSCBS-0003 | `NOT_READY — REFERENCE_LOOKUP_UNAVAILABLE` | `NOT_READY — STATUS_NOT_APPROVED` |

O comando real não conseguiu consultar as referências governadas porque o PostgreSQL local estava
indisponível. A validação estrutural automatizada, com referências controladas como existentes e
publicadas, confirmou que os três documentos são válidos e permanecem bloqueados pelo status
`DRAFT`. Nenhum resultado autoriza implementação.

## Confirmação final

Não existe `TaxRuleVersion` real para essas especificações, não existe ruleset tributário real
publicado e nenhuma das regras `RT-IBSCBS-0001`, `RT-IBSCBS-0002` ou `RT-IBSCBS-0003` está
disponível para execução pelo `tax-engine`.
