# Produto e enquadramento assistido IBS/CBS

## O que esta etapa faz

A plataforma cadastra produtos por organização, preserva cada versão tributariamente relevante e
monta um FactSet determinístico para avaliação. O motor pode representar candidatos CST/cClassTrib,
fatos ausentes, conflitos e DecisionTrace, sempre apontando para versões exatas de regra, ruleset e
catálogo.

Nesta entrega não existe regra tributária real aprovada para execução. Os testes conclusivos usam
somente jurisdição, fontes, atributos e códigos explicitamente sintéticos. Em operação, a ausência
de regra aprovada impede uma conclusão real.

## Produto e histórico

Código interno, descrição e unidade são obrigatórios. GTIN, NCM e CEST são opcionais porque sua
ausência não pode impedir o cadastro e sua presença não determina tributação. Cada alteração cria
`ProductVersion` imutável com hash. Atributos fiscais são registros ligados à versão e, nesta fase,
somente o namespace `synthetic.*` é aceito pela API.

Uma classificação não é gravada como campo eterno do produto. A avaliação guarda o snapshot do
FactSet, `product_version_id`, data da operação, catálogo, ruleset, regras, resultado e trace.

## Fluxo de consulta

```text
produto atual ou fatos manuais
  → catálogo PUBLISHED e ruleset PUBLISHED
  → seleção temporal de regras
  → avaliação de condições
  → validação CST/cClassTrib no mesmo snapshot
  → CONCLUSIVO | POSSIVEIS_ENQUADRAMENTOS
    | NECESSITA_VALIDACAO | SEM_CLASSIFICACAO
  → avaliação histórica + DecisionTrace
```

Fato manual que contradiga o cadastro é rejeitado; não há sobrescrita silenciosa. Fatos ausentes
são caminhos canônicos que a interface poderá transformar em perguntas. Dois resultados distintos
sem precedência aprovada permanecem como alternativas.

## Trava para regras reais

Uma regra real precisa de documento em `docs/tax/rules/` baseado no template, fonte oficial,
vigência, fatos, condições, CST/cClassTrib, testes positivos/negativos/inconclusivos e aprovação
humana identificada. Depois disso ainda será necessário cadastrar e publicar a fonte, a versão da
regra e o ruleset, e implementar um adaptador allowlisted com testes.

## Limitações

- NCM, GTIN, CEST e descrição não são classificadores absolutos.
- Não há cálculo financeiro, crédito, redução, Split Payment, XML ou SPED.
- Não há importação em massa de produtos.
- `ProductTaxReview` está modelado, mas a recomendação automática de reavaliação não foi ativada.
- IA não participa da decisão determinística nem resolve conflitos.
