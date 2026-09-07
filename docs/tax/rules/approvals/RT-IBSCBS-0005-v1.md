# Evidência de revisão e aprovação — RT-IBSCBS-0005 v1

- **Especificação:** RT-IBSCBS-0005
- **Versão:** 1
- **Data da declaração:** 2026-09-07
- **Revisor e aprovador:** Guilherme Nunes
- **Capacidade declarada:** responsável tributário e jurídico do projeto
- **Ator governado:** `legal-approver-guilherme-nunes`
- **Escopo:** art. 146, § 1º, II, da LC nº 214/2025 (medicamento registrado na Anvisa adquirido
  por entidade de saúde imune ao IBS e à CBS, com CEBAS válido e comprovação do requisito legal de
  prestação de serviços ao SUS nos termos dos arts. 9º a 11 da LC nº 187/2021), com DecisionTrace e
  fundamento mantidos separados da hipótese do inciso I (RT-IBSCBS-0003), ainda que a classificação
  oficial (cClassTrib 200010) coincida.

## Declaração registrada

O responsável declarou aprovação integral da especificação v1 da RT-IBSCBS-0005, conforme
delimitada no próprio documento de especificação
(`docs/tax/rules/specifications/RT-IBSCBS-0005.json`), e autorizou o registro da mesma pessoa nos
campos `reviewed_by` e `approved_by`.

Permanecem expressamente fora desta aprovação, conforme já registrado em `known_conflicts` na
própria especificação: (1) qualquer combinação desta regra jurídica com a do inciso I
(RT-IBSCBS-0003) apenas por coincidência de cClassTrib — a coincidência da classificação oficial
não autoriza fundir as hipóteses, que devem permanecer executáveis e rastreáveis separadamente; e
(2) os tipos específicos de evidência documental aceitos como suficientes para comprovar imunidade,
CEBAS e o requisito legal do SUS, que continuam exigindo julgamento humano caso a caso e não são
definidos por esta especificação.

Esta aprovação **não autoriza, por si só, implementação, publicação de `TaxRuleVersion` ou
alteração de qualquer ruleset**. A avaliação de implementação depende dos demais requisitos
estruturais do pré-flight real (fonte legal e versão de catálogo governadas e resolvíveis nesta
instância de banco), e a regra deve ser implantada em ruleset explícito próprio, distinto do
ruleset `IBSCBS-PILOT-001` já publicado para RT-IBSCBS-0003, para preservar rastreabilidade e
evitar o risco de agregação indevida entre hipóteses jurídicas distintas.

Esta evidência não contém CPF, documento pessoal, credencial ou segredo. O hash desta evidência
será referenciado no campo `approval.approval_evidence` da especificação no momento da promoção;
qualquer alteração posterior exige nova versão e nova aprovação.
