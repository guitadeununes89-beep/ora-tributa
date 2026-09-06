# Matriz de prontidão para aprovação jurídica final — Etapa 7B.3

## Critério de leitura

Esta matriz é documental e não altera o lifecycle. Todas as especificações permanecem `DRAFT`.
`Pronta para revisão final` significa que as referências técnicas estão resolvidas e que o texto
pode ser submetido ao gate humano indicado; não significa `APPROVED`, implementação autorizada ou
correção jurídica atestada.

| Rule ID | Fundamento | Vigência | CST | cClassTrib | Fonte | Referências resolvidas | Bloqueador jurídico | Pronta para revisão final |
|---|---|---|---|---|---|---|---|---|
| RT-IBSCBS-0001 | LC nº 214/2025, arts. 133 e 146 | desde 01/01/2026 | 200 | 200032 | LC 214 compilada; LC 227 separada | SIM — fonte `23302183-6c92-4b34-a26d-cd272e2c1b1e`; catálogo `2295b90f-2f92-4fa4-8181-3007f02b1679` PUBLISHED | Entidade do art. 133, § 2º; suficiência da prova; cobertura integral das hipóteses de zero | NÃO — classe B |
| RT-IBSCBS-0002 | LC nº 214/2025, art. 146, caput, I–VII e § 3º | desde 14/01/2026 | 200 | 200009 | LC 214 compilada; LC 227 separada | SIM — fonte e catálogo 2026-06-23 PUBLISHED | Lista oficial temporal do § 3º e confirmação de sua função jurídica | NÃO — classe C |
| RT-IBSCBS-0003 | LC nº 214/2025, art. 146, § 1º, I | desde 01/01/2026 | 200 | 200010 | LC 214 compilada; LC 227 separada | SIM — fonte e catálogo 2026-06-23 PUBLISHED | Revisão humana final do recorte e da descrição compartilhada 200010 | SIM — classe A; somente submissão humana |
| RT-IBSCBS-0004 | LC nº 214/2025, art. 146 original e Anexo XIV | 01/01/2026 a 13/01/2026 | 200 | 200009 | LC 214 original; catálogo NF-e 2025-12-15 | SIM — fonte `052c8ce0-2e4c-4422-a86f-1f6977ba2ef6`; catálogo `c79f28ea-c741-42e7-a339-8016fb31cefd` PUBLISHED | Conferência individual e temporal do Anexo XIV | NÃO — classe B |
| RT-IBSCBS-0005 | LC nº 214/2025, art. 146, § 1º, II; LC nº 187/2021 | desde 01/01/2026 | 200 | 200010 | LC 214 compilada; LC 187 separada | SIM — fonte e catálogo 2026-06-23 PUBLISHED | Requisitos e evidências para imunidade, CEBAS, SUS e adquirente efetivo | NÃO — classe B |
| RT-IBSCBS-0006 | LC nº 214/2025, art. 146, § 1º, III e § 3º | desde 14/01/2026 | 200 | 200053 | LC 214 compilada; LC 227 separada | SIM — fonte e catálogo 2026-06-23 PUBLISHED | Regulamentação sanitária oficial e lista oficial temporal do § 3º | NÃO — classe C |

## Priorização A/B/C

- **A — submetível à revisão jurídica humana final:** `RT-IBSCBS-0003`.
- **B — depende de confirmação normativa adicional:** `RT-IBSCBS-0001`, `RT-IBSCBS-0004` e
  `RT-IBSCBS-0005`.
- **C — depende de nova fonte ou regulamentação oficial:** `RT-IBSCBS-0002` e
  `RT-IBSCBS-0006`.

O preflight das seis retorna `NOT_READY` apenas por `STATUS_NOT_APPROVED`. Classe A é uma fila de
revisão humana, não um estado técnico e não autoriza `TaxRuleVersion` ou ruleset.
