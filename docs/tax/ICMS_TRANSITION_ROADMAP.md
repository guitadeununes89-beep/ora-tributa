# Roadmap de transição — ICMS

## Objetivo

Preparar a coexistência do ICMS com IBS/CBS sem implementar cálculo estadual nesta etapa. O ICMS
continua sendo um domínio próprio; não será absorvido por regras de IBS.

## Marcos

| Período | Marco constitucional | Trabalho futuro obrigatório |
|---|---|---|
| 2026–2028 | ICMS permanece no sistema vigente | inventário por UF, operação, regime e benefício; fontes oficiais versionadas |
| 2029 | 9/10 das alíquotas então aplicáveis | regra temporal, parâmetros estaduais e testes de benefícios |
| 2030 | 8/10 | nova versão temporal, sem sobrescrever 2029 |
| 2031 | 7/10 | nova versão temporal, sem sobrescrever períodos anteriores |
| 2032 | 6/10 | última versão coexistente antes da extinção |
| 2033 em diante | extinção do ICMS | preservar reprocessamento histórico; não apagar regras anteriores |

Fundamento: [EC 132/2023](https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm),
ADCT, arts. 128 e 129.

## Frentes de modelagem

- legislação e alíquotas por UF, operação e vigência;
- origem, destino, estabelecimento, destinatário, regime e finalidade;
- benefícios/incentivos e sua redução proporcional, sem aplicação genérica;
- créditos e estornos próprios;
- interação com IBS, CBS, IS, IPI e ICMS-ST;
- trilhas de decisão e cálculo reproduzíveis.

## Bloqueios atuais

Não há base estadual governada, regra aprovada, parâmetro de alíquota nem ruleset de ICMS. As
frações constitucionais não bastam para calcular uma operação. Ausência de regra deve resultar em
incerteza explícita.
