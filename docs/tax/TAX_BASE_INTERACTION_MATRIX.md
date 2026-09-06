# Matriz de interação entre bases tributárias

## Objetivo

Registrar interações normativas conhecidas sem convertê-las em regra produtiva. Cada linha futura
deverá originar uma `TaxInteractionRule` versionada, com vigência, dispositivo, fonte governada e
teste. `INCLUDED` e `EXCLUDED` abaixo descrevem o texto normativo; `PENDING` impede conclusão.

| Tributo calculado | Tributo relacionado | Entra na base? | Período | Fundamento | Status |
|---|---|---|---|---|---|
| IBS/CBS | próprio IBS e CBS | Não | Regra geral | LC 214/2025 compilada, art. 12, § 2º, I | Confirmado; não implementado |
| IBS/CBS | ICMS e ISS | Não | 2026-01-01 a 2032-12-31 | LC 214/2025 compilada, art. 12, § 2º, V | Confirmado; não implementado |
| IBS/CBS | PIS e Cofins | Não | 2026-01-01 a 2032-12-31 | LC 214/2025 compilada, art. 12, § 2º, V | Confirmado; não implementado |
| IBS/CBS | Imposto Seletivo | Sim | Regra constitucional geral | Constituição, art. 153, § 6º, IV; LC 214/2025, art. 12 | Confirmado; não implementado |
| IBS/CBS — importação | Imposto de Importação e Imposto Seletivo | Sim | Importação | LC 214/2025 compilada, art. 69 | Confirmado; não implementado |
| IBS/CBS — importação | IPI, ICMS e ISS | Não | Importação | LC 214/2025 compilada, art. 69, § 2º | Confirmado; não implementado |
| Imposto Seletivo | CBS, IBS e próprio IS | Não | Regra geral da base do IS | LC 214/2025 compilada, art. 417, I | Confirmado; não implementado |
| Imposto Seletivo | ICMS e ISS | Não | Até 2032-12-31 | LC 214/2025 compilada, art. 417, § 4º | Confirmado; não implementado |
| Imposto Seletivo | PIS/Cofins ou outras parcelas não listadas | Pendente | Conforme operação | Não consolidado nesta etapa | Bloqueado; não inferir |
| ICMS/ISS | IBS, CBS e IS | Pendente | Legislação de cada tributo e período | Não consolidado nesta etapa | Bloqueado; não inferir simetria |

Fontes oficiais: [Constituição/EC 132](https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm),
[LC 214/2025 compilada](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm) e
[LC 227/2026](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm).

## Regras de segurança

1. A matriz não implica cálculo “por dentro” ou “por fora” além do dispositivo indicado.
2. Ausência de uma linha aplicável não significa exclusão, inclusão ou não incidência.
3. A base de uma importação não é presumida igual à de operação interna.
4. Uma alteração temporal cria nova versão da interação; não sobrescreve histórico.
5. A consolidação só soma resultados `CALCULATED`; pendências permanecem visíveis por tributo.
