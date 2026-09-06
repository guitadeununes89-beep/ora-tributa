# Matriz normativa da transição tributária — 2026 a 2033

## Escopo e controle

Esta matriz descreve o calendário constitucional em vigor na data de revisão, **2026-09-02**. Ela
não é ruleset, não contém configuração produtiva e não autoriza cálculo. A execução futura exige
`TaxTransitionPeriod` persistido, fonte governada, versão, teste e publicação.

Fontes oficiais:

- [Emenda Constitucional nº 132/2023](https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm), ADCT, arts. 124 a 133;
- [Receita Federal — Entenda a Reforma Tributária do Consumo](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/entenda), síntese institucional do cronograma;
- [Lei Complementar nº 214/2025 compilada](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm);
- [Lei Complementar nº 227/2026](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm), alterações posteriores aplicáveis.

## Períodos normativos

| Período | IBS/CBS | ICMS/ISS | Imposto Seletivo | Fundamento principal | Estado no motor |
|---|---|---|---|---|---|
| 2026 | IBS estadual de 0,1% e CBS de 0,9%, conforme regras constitucionais de teste e compensação | Permanecem no sistema atual | Ainda não indicado como cobrança no art. 126 | ADCT, arts. 125 e 133 | Apenas documentado; não executável |
| 2027 | IBS: 0,05% estadual e 0,05% municipal; redução de 0,1 ponto percentual na alíquota de referência da CBS | Permanecem no sistema atual | Cobrança a partir de 2027; depende de alíquotas instituídas por lei ordinária | ADCT, arts. 126 e 127 | Apenas documentado; alíquota de IS ausente |
| 2028 | Mantém a disciplina constitucional de 2027 para IBS/CBS indicada no art. 127 | Permanecem no sistema atual | Domínio separado; depende de regras e alíquotas publicadas | ADCT, art. 127 | Período próprio, apenas documentado |
| 2029 | Início da substituição gradual; síntese institucional: 10% do IBS de transição | ICMS/ISS: 9/10 das alíquotas então aplicáveis | Domínio separado | ADCT, art. 128, I | Apenas documentado |
| 2030 | Síntese institucional: 20% do IBS de transição | ICMS/ISS: 8/10 | Domínio separado | ADCT, art. 128, II | Apenas documentado |
| 2031 | Síntese institucional: 30% do IBS de transição | ICMS/ISS: 7/10 | Domínio separado | ADCT, art. 128, III | Apenas documentado |
| 2032 | Síntese institucional: 40% do IBS de transição | ICMS/ISS: 6/10 | Domínio separado | ADCT, art. 128, IV | Apenas documentado |
| 2033 em diante | Novo modelo plenamente vigente, sujeito às regras e alíquotas publicadas aplicáveis | ICMS e ISS extintos | Domínio separado | ADCT, art. 129 | Apenas documentado |

Os percentuais de 10%, 20%, 30% e 40% acima descrevem a proporção da transição apresentada pela
Receita Federal; não são alíquotas nominais de uma operação. As alíquotas de referência seguem o
mecanismo do ADCT, art. 130, e não podem ser deduzidas por esta matriz.

## Invariantes de implementação futura

- O frontend consulta os períodos; não contém `if` por ano nem percentuais normativos.
- Mudança de redação ou parâmetro cria nova versão e preserva a versão anterior.
- A data da operação seleciona a vigência jurídica; a data de conhecimento seleciona a versão que
  o sistema conhecia no reprocessamento bitemporal.
- Ausência de alíquota, interação ou regra publicada resulta em `REQUIRES_VALIDATION`, nunca zero.
- Incentivos e benefícios de ICMS/ISS mencionados no art. 128 exigem regras próprias; a fração anual
  não pode ser aplicada genericamente sem validar a hipótese jurídica.

## Limitações

Não foram cadastradas regras executáveis, alíquotas de referência, parâmetros por ente federativo,
créditos, benefícios ou arredondamentos. A matriz não substitui revisão jurídica na data da futura
implementação.
