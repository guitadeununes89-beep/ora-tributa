# Roadmap nacional de cobertura IBS/CBS

> Este é o eixo A do [roadmap consolidado do motor tributário](TAX_ENGINE_CONSOLIDATED_ROADMAP.md).
> Imposto Seletivo e transição ICMS/ISS possuem roadmaps próprios; avanço aqui não autoriza cálculo
> nos outros eixos.

## Critério

O roadmap parte do catálogo oficial `2026-06-23`, não de setores comerciais. Os cinco blocos abaixo
correspondem exatamente ao atributo oficial **Tipo de Alíquota**; juntos somam os 164 cClassTrib.
Prioridade considera amplitude normativa, complexidade, fontes adicionais e risco. Não há dados de
participação de mercado no repositório, portanto nenhuma prioridade afirma alcance econômico.

| Prioridade | Família oficial | cClassTrib | CST | Dispositivos distintos | Fatos esperados | Dependências | Dificuldade | Risco | Automação |
|---|---|---:|---|---:|---|---|---|---|---|
| P1 | Padrão | 61 | 000, 200, 222, 515 | 60 | objeto, operação, partes, vigência e condições específicas | alíquotas de referência; anexos quando citados | média/alta e heterogênea | alto se descrição virar regra | possível somente após decomposição por dispositivo |
| P2 | Sem alíquota | 83 | 400, 410, 510, 550, 620, 800, 810, 811, 820, 830 | 81 | não incidência, imunidade, suspensão, diferimento, crédito e evento operacional | atos complementares, documentos e listas oficiais | alta | muito alto por exceções e temporalidade | parcial, com forte validação jurídica |
| P3 | Uniforme setorial | 8 | 010, 620 | 7 | natureza da operação, período, base específica e parte qualificada | alíquotas oficiais por período e regulamentação | alta | alto | baixa antes das tabelas complementares |
| P3 | Fixa | 7 | 220, 221 | 4 | unidade de medida, quantidade, produto/operação e período | tabela oficial de valor fixo e atualizações | alta | alto por cálculo e vigência | possível após ingestão de valores oficiais |
| P4 | Uniforme nacional (referência) | 5 | 011 | 5 | regime específico, base, parte e período | alíquotas de referência e regras setoriais | muito alta | muito alto | baixa inicialmente |

## Sequência por fundamento

1. dentro de P1, decompor os 60 dispositivos oficiais em famílias jurídicas sem agregar por setor;
2. selecionar especificações de menor dependência externa e validar fatos canônicos reutilizáveis;
3. em P2, separar não incidência, imunidade, suspensão, diferimento e crédito antes de escrever regras;
4. ingerir tabelas complementares governadas antes de P3/P4;
5. medir alcance somente quando houver dados auditáveis de operações, sem transformar amostra em
   fundamento jurídico.

## Gate por bloco

`catálogo → fonte/dispositivo → família jurídica → especificação DRAFT → revisão humana → APPROVED
→ implementação testada → TaxRuleVersion PUBLISHED → ruleset explícito`.

Nenhuma linha deste roadmap autoriza regra nova.
