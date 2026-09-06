# Matriz de cobertura do art. 146 — Etapa 7B.1

## Finalidade

Esta matriz impede que `RT-IBSCBS-0001` produza `NOT_ELIGIBLE` para alíquota zero enquanto alguma
hipótese do art. 146 temporalmente aplicável não tiver sido avaliada. Ela é documental e não amplia o escopo executável: somente a linha
explicitamente `APPROVED` possui implementação e publicação governadas.

## Regra de fechamento da cobertura

`operation.art_146_coverage_status` somente poderá ser `COMPLETE` quando todas as linhas aplicáveis
à data da operação tiverem especificação aprovada, dados suficientes e resultado rastreável. Na
presença de lacuna, ato não localizado, regulamentação pendente ou fato desconhecido, o estado deve
permanecer `INCOMPLETE` ou `UNKNOWN` e `RT-IBSCBS-0001` deve retornar necessidade de validação.

## Redação original — 01/01/2026 a 13/01/2026

| Dispositivo | Hipótese | Regra | Status | CST | cClassTrib | Bloqueadores |
|---|---|---|---|---|---|---|
| caput e Anexo XIV | Medicamentos relacionados no Anexo XIV, conforme NCM/SH | `RT-IBSCBS-0004` | `DRAFT` | 200 | 200009 | Fonte e catálogo histórico sem IDs governados vinculados; conferência individual do Anexo XIV |
| § 1º, I | Medicamentos registrados adquiridos por administração direta, autarquia ou fundação pública | `RT-IBSCBS-0003` | `APPROVED` | 200 | 200010 | Implementada exclusivamente no ruleset piloto explícito |
| § 1º, II | Medicamentos registrados adquiridos por entidade de saúde imune com CEBAS e requisito SUS | `RT-IBSCBS-0005` | `DRAFT` | 200 | 200010 | Evidências canônicas; vínculos governados; revisão e aprovação |
| § 2º | Composições do Anexo VI adquiridas pelos órgãos e entidades do § 1º | `RT-IBSCBS-0007` proposta, não criada | LACUNA | a confirmar temporalmente | a confirmar temporalmente | Especificação jurídica própria e catálogo temporal governado |
| § 3º | Revisão anual do Anexo XIV na redação original | dependência de `RT-IBSCBS-0004` | LACUNA DOCUMENTAL | — | — | Eventual ato conjunto histórico aplicável e versão do Anexo XIV |
| § 4º | Inclusão temporária por emergência de saúde pública | especificação por ato; `RT-IBSCBS-0008` reservada conceitualmente | LACUNA | a confirmar temporalmente | a confirmar temporalmente | Emergência reconhecida, ato conjunto, período e localidade |

## Redação da LC nº 227/2026 — desde 14/01/2026

| Dispositivo | Hipótese | Regra | Status | CST | cClassTrib | Bloqueadores |
|---|---|---|---|---|---|---|
| caput, I–VII | Medicamento registrado destinado conforme registro sanitário às sete finalidades legais | `RT-IBSCBS-0002` | `DRAFT` | 200 | 200009 | `NEEDS_ART146_PAR3_OFFICIAL_LIST`; vínculos governados; vocabulário e aprovação |
| § 1º, I | Aquisição por administração direta, autarquia ou fundação pública | `RT-IBSCBS-0003` | `APPROVED` | 200 | 200010 | Implementada exclusivamente no ruleset piloto explícito |
| § 1º, II | Aquisição por entidade de saúde imune com CEBAS e requisito SUS | `RT-IBSCBS-0005` | `DRAFT` | 200 | 200010 | Evidências canônicas; vínculos governados; revisão e aprovação |
| § 1º, III | Soro ou vacina conforme regulamentação sanitária específica | `RT-IBSCBS-0006` | `DRAFT` | 200 | 200053 | `NEEDS_OFFICIAL_SANITARY_REGULATION`; `NEEDS_ART146_PAR3_OFFICIAL_LIST`; vínculos governados |
| § 2º | Composições do Anexo VI adquiridas pelos órgãos e entidades do § 1º | `RT-IBSCBS-0007` proposta, não criada | LACUNA | 200 | 200011 | Especificação própria, critérios do Anexo VI e evidências dos adquirentes |
| § 3º | Lista periódica do caput e do § 1º, III | dependência de `RT-IBSCBS-0002` e `RT-IBSCBS-0006` | BLOQUEADOR | — | — | `NEEDS_ART146_PAR3_OFFICIAL_LIST` |
| § 4º | Inclusão temporária por emergência de saúde pública | especificação por ato; `RT-IBSCBS-0008` reservada conceitualmente | LACUNA | 200 | 200012 | Emergência reconhecida, ato conjunto, vigência e linhas de cuidado |

## Especificações adicionais necessárias

- `RT-IBSCBS-0007`: art. 146, § 2º, com Anexo VI e adquirentes dos incisos I e II;
- uma especificação temporal por ato do § 4º; `RT-IBSCBS-0008` é apenas reserva conceitual e não
  corresponde a documento criado;
- eventual versão de `RT-IBSCBS-0004` se for localizado ato histórico que tenha alterado o Anexo XIV.

Enquanto essas lacunas existirem, a cobertura agregada do art. 146 não pode ser declarada completa.



