# Relatório de carga governada — Etapa 7B.3

## Resultado executivo

A causa do banco vazio era operacional: as migrações criavam o schema, mas nenhum seed normativo
ou comando de implantação executava o pipeline de catálogo. Os artefatos e manifestos existiam no
Git, porém nunca haviam sido importados no PostgreSQL.

A etapa criou a organização fictícia `dev-governance-org`, sem empresa real, e três atores
segregados: `dev-curator` (`CURATOR`), `dev-approver` (`APPROVER`) e `dev-publisher`
(`PUBLISHER`). A carga foi executada duas vezes e retornou os mesmos IDs, contagens e hashes.

## Fontes legais oficiais persistidas

| Fonte | legal_source_id | SHA-256 do snapshot |
|---|---|---|
| LC 214/2025 compilada | `23302183-6c92-4b34-a26d-cd272e2c1b1e` | `aacfd146f2c91291c3c8675035da70cb08b359bca03b3ccc21c5b3a14e6a7719` |
| LC 214/2025 original | `052c8ce0-2e4c-4422-a86f-1f6977ba2ef6` | `efd06578a4789874fd277c3dbf68d424cd9b4baebc1a853735ec350b692ecd29` |
| LC 227/2026 | `ac83ca28-652a-4ac3-9902-505c09edeb4d` | `dbf1f092f86762db88db9bbf142fa772ea8e16cbc360e80bb49a258c2ac4ae8d` |
| LC 187/2021 | `348061c6-69b1-4f3d-9cc9-cac7e6e7fb31` | `178977d307bb0a7bf71889b98160f9fc001621918407a4cd3bd87fe8fc6e287d` |

Os textos original e compilado da LC 214 foram preservados separadamente. LC 227 e LC 187 não
substituem a fonte principal nem alteram silenciosamente a interpretação das especificações.

## Catálogo IBS/CBS publicado

`catalog_id`: `731fb573-f26c-49eb-bfb6-d479b410ea98`.

| Versão | catalog_version_id | Status | Hash do artefato | Fingerprint normalizado | Linhas da planilha | Staging | CST válidos/distintos | cClassTrib válidas/distintas | Rejeições/duplicatas |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| 2025-12-15 | `c79f28ea-c741-42e7-a339-8016fb31cefd` | PUBLISHED | `15ce63cbbe53b5b00fc5e61e775221984a910dcdab547fd130d2ad0c478c7e46` | `18eb581eca9ac621b30ed2fc51f30c279b3dbbbe8bef513777afdbd80485729c` | 169 | 166 | 18/18 | 145/145 | 0/0 |
| 2026-06-23 | `2295b90f-2f92-4fa4-8181-3007f02b1679` | PUBLISHED | `1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654` | `9b65c977cdd37b30f0146b10f8addd7175f11389fc08196a9dfebfd5258b2008` | 188 | 185 | 18/18 | 164/164 | 0/0 |

“Linhas da planilha” inclui cabeçalhos, linha vazia e legendas. O staging exclui cabeçalhos e a
linha inteiramente vazia, preservando as três legendas do CST. Cada versão possui cinco eventos:
importação, validação, envio à revisão, aprovação e publicação. A publicação ocorreu em
30/08/2026 por `dev-publisher`; aprovação por `dev-approver`; importação/revisão por `dev-curator`.

O CST 200 e as cClassTrib 200009, 200010 e 200032 existem nas duas versões. A cClassTrib 200053
existe na versão 2026-06-23. Todas estão estruturalmente associadas ao CST 200.

## Referências das especificações e preflight

- `RT-IBSCBS-0004` referencia a LC 214 original e o catálogo histórico 2025-12-15.
- `RT-IBSCBS-0001`, `0002`, `0003`, `0005` e `0006` referenciam a LC 214 compilada e o catálogo
  2026-06-23.
- As fontes complementares LC 227/2026 e LC 187/2021 estão persistidas separadamente. O contrato
  atual possui uma fonte principal por especificação; sua existência não amplia o sentido jurídico.

| Rule ID | Status | Preflight | Issues restantes |
|---|---|---|---|
| RT-IBSCBS-0001 | DRAFT | NOT_READY | STATUS_NOT_APPROVED |
| RT-IBSCBS-0002 | DRAFT | NOT_READY | STATUS_NOT_APPROVED |
| RT-IBSCBS-0003 | DRAFT | NOT_READY | STATUS_NOT_APPROVED |
| RT-IBSCBS-0004 | DRAFT | NOT_READY | STATUS_NOT_APPROVED |
| RT-IBSCBS-0005 | DRAFT | NOT_READY | STATUS_NOT_APPROVED |
| RT-IBSCBS-0006 | DRAFT | NOT_READY | STATUS_NOT_APPROVED |

`SOURCE_NOT_FOUND` e `CATALOG_VERSION_NOT_FOUND` desapareceram. `NOT_READY` continua correto: o
comando existente não possui `READY_FOR_LEGAL_APPROVAL`, e o ADR-0016 proíbe transformar esse gate
documental em aprovação ou prontidão de implementação.

## Prontidão jurídica remanescente

- **A — submetível à revisão jurídica humana final:** `RT-IBSCBS-0003`.
- **B — requer confirmação normativa adicional:** `RT-IBSCBS-0001`, `RT-IBSCBS-0004` e
  `RT-IBSCBS-0005`.
- **C — requer fonte ou regulamentação oficial adicional:** `RT-IBSCBS-0002` e
  `RT-IBSCBS-0006`.

Bloqueadores: entidade e prova do art. 133, § 2º (`0001`); lista oficial do art. 146, § 3º
(`0002`); conferência temporal individual do Anexo XIV (`0004`); imunidade, CEBAS, SUS e adquirente
efetivo (`0005`); regulamentação sanitária e lista do § 3º (`0006`). Nenhuma lacuna foi preenchida
por inferência.

## Validações e limites

- carga repetida sem criar duplicatas ou novos IDs;
- 67 testes Python aprovados e 1 teste geral condicionado ao PostgreSQL;
- teste PostgreSQL de imutabilidade executado separadamente e aprovado;
- Ruff e mypy aprovados nos arquivos alterados;
- inventário final: 6 fontes oficiais (4 legais e 2 técnicas), 4 eventos de auditoria das fontes,
  10 eventos de lifecycle dos catálogos, 0 `TaxRuleVersion` real e 0 rulesets.

Nenhuma especificação foi promovida para `APPROVED` ou `IMPLEMENTED`. Nenhuma regra tributária real
está executável pelo `tax-engine`.
