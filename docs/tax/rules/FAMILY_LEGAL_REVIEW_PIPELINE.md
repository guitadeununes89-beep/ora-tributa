# Pipeline reutilizável de revisão jurídica por família

`FAMILY → SOURCE CHECK → SPEC → LEGAL REVIEW → BLOCKERS → HUMAN APPROVAL → IMPLEMENTATION → PUBLICATION`

| Gate | Entrada mínima | Saída auditável | Proibição |
|---|---|---|---|
| FAMILY | recorte documental e códigos do catálogo | justificativa da família sem presumir 1:1 | família não vira regra |
| SOURCE CHECK | fontes oficiais, versões, hashes e vigência | matriz literal de dispositivos e divergências | fonte secundária não fundamenta regra |
| SPEC | fatos juridicamente necessários | especificações versionadas em DRAFT e casos de teste | não preencher lacuna por inferência |
| LEGAL REVIEW | especificação e fontes | A, B ou C, com responsável e evidência | não aprovar automaticamente |
| BLOCKERS | divergências e dependências | bloqueadores explícitos, separando jurídico e técnico | não ocultar conflito |
| HUMAN APPROVAL | parecer humano formal | APPROVED somente por ato autorizado | aprovação não publica |
| IMPLEMENTATION | especificação aprovada | TaxRuleVersion testada e rastreável | tax-engine não interpreta além da spec |
| PUBLICATION | versão testada e segregação de funções | ruleset imutável e reproduzível | não sobrescrever histórico |

## Checklist por lote

- fonte e catálogo estão `PUBLISHED`, com IDs reais e fingerprints;
- redação original, compilada e alterações foram comparadas;
- `effective_from` e `effective_to` foram confirmados;
- FactSet não usa NCM, CEP, UF ou descrição isoladamente;
- há pelo menos três casos positivos, três negativos e três inconclusivos;
- limites temporais e territoriais foram cobertos;
- precedência só foi declarada com fundamento expresso;
- DRAFT, pronto para revisão, bloqueado, aprovado e publicado permanecem conceitos distintos;
- aprovação, implementação e publicação exigem atos separados.

## Aplicação ao lote P1 ZFM/ALC

| Regra | Source check | Spec | Legal review | Bloqueadores | Próximo gate |
|---|---|---|---|---|---|
| RT-IBSCBS-0007 | revalidado | v3 DRAFT | `READY_FOR_HUMAN_APPROVAL` | nenhum no escopo nacional; extensão estrangeira fora do escopo | aprovação humana |
| RT-IBSCBS-0008 | revalidado | v3 DRAFT | `READY_FOR_HUMAN_APPROVAL` | nenhum bloqueador jurídico remanescente | aprovação humana |
| RT-IBSCBS-0009 | revalidado | v3 DRAFT | `BLOCKED` | conflito literal 200024: art. 456 × art. 460 | fonte oficial corretiva/confirmatória |
