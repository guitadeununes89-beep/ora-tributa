# Roadmap de transição — ISS

## Objetivo

Preparar a coexistência do ISS com IBS/CBS sem implementar cálculo municipal nesta etapa. ISS e
IBS permanecem domínios distintos durante a transição e no histórico.

## Marcos

| Período | Marco constitucional | Trabalho futuro obrigatório |
|---|---|---|
| 2026–2028 | ISS permanece no sistema vigente | fontes municipais, lista de serviços, local da incidência, regime e benefício |
| 2029 | 9/10 das alíquotas então aplicáveis | regra temporal e parâmetros do município competente |
| 2030 | 8/10 | nova versão temporal |
| 2031 | 7/10 | nova versão temporal |
| 2032 | 6/10 | última versão coexistente |
| 2033 em diante | extinção do ISS | reprocessamento histórico preservado |

Fundamento: [EC 132/2023](https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm),
ADCT, arts. 128 e 129.

## Frentes de modelagem

- serviço/direito/operação e item legal aplicável;
- município competente, estabelecimento e local da prestação;
- alíquota, retenção, regime e benefício por vigência;
- interação de base com IBS, CBS e IS;
- créditos ou ajustes quando previstos;
- `DecisionTrace` e `CalculationTrace` separados.

## Bloqueios atuais

Não há fontes municipais governadas nem ruleset de ISS. A fração anual constitucional não fornece
sozinha a alíquota de uma operação. Nenhuma resposta produtiva deve assumir zero ou repetir regra de
IBS como substituta.
