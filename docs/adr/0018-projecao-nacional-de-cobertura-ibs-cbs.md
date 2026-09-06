# ADR-0018 — Projeção nacional de cobertura IBS/CBS

- **Estado:** Aceito
- **Data:** 2026-09-01
- **Relacionados:** ADR-0006, ADR-0010, ADR-0013, ADR-0015 e ADR-0017

## Contexto

O catálogo oficial governado contém 164 cClassTrib, enquanto o motor possui uma única regra real
publicada. Organizar a expansão pelo primeiro piloto — medicamentos — ocultaria a dimensão nacional
do catálogo e poderia induzir uma falsa relação entre cClassTrib e regra tributária.

A plataforma precisa exibir cobertura verificável sem transformar descrições do catálogo em regras,
sem duplicar o lifecycle existente e sem persistir uma segunda fonte de verdade sujeita a drift.

## Decisão

1. A cobertura nacional será uma projeção de leitura, derivada do `CatalogVersion PUBLISHED`, das
   especificações jurídicas canônicas e das `TaxRuleVersion` governadas.
2. O catálogo continua sendo a fonte dos códigos, descrições, vigência, indicadores e referências
   técnicas oficiais. Esses dados não constituem, isoladamente, regra executável.
3. A projeção não cria tabela própria nesta etapa. API, dashboard e relatório usam o mesmo serviço
   determinístico e podem ser regenerados a partir das fontes governadas.
4. Os estados de cobertura são: `CATALOG_ONLY`, `LEGAL_MAPPING_REQUIRED`,
   `DRAFT_SPECIFICATION`, `LEGAL_REVIEW`, `APPROVED`, `IMPLEMENTED`, `PUBLISHED` e
   `BLOCKED_EXTERNAL_SOURCE`.
5. Estados reutilizam o lifecycle quando há especificação ou versão. `LEGAL_MAPPING_REQUIRED`
   significa que o catálogo aponta fundamento, mas ainda não existe especificação jurídica.
   `CATALOG_ONLY` significa ausência de dispositivo oficial estruturado no snapshot.
6. A associação é muitos-para-muitos por natureza: uma especificação/regra referencia um
   cClassTrib, várias regras podem compartilhar o mesmo código e uma família jurídica pode abranger
   vários códigos. Nenhuma constraint 1:1 será criada.
7. `PUBLISHED` em um código significa que existe ao menos uma regra publicada associada; não afirma
   cobertura integral de todas as hipóteses jurídicas possíveis daquele cClassTrib. A interface
   exibirá essa limitação.
8. Percentuais usam contagem de códigos distintos sobre o total do snapshot e representação decimal
   textual, sem `float` e sem arredondamento que oculte o denominador.
9. Famílias jurídicas são agrupadas apenas por dispositivo/fundamento oficial presente no catálogo.
   Setores comerciais não serão inferidos.

## Consequências

- os 164 códigos ficam visíveis sem gerar 164 regras;
- catálogo, especificações e regras mantêm papéis distintos e auditáveis;
- mudanças no snapshot alteram a projeção somente após publicação governada;
- o dashboard pode informar 1/164 publicado sem sugerir cobertura nacional completa;
- bloqueadores e múltiplas regras por código permanecem visíveis.

## Alternativas consideradas

1. **Persistir uma tabela de cobertura editável:** rejeitada nesta etapa por duplicar estado derivável.
2. **Tratar cada cClassTrib como uma TaxRule:** rejeitada por incorreção jurídica e cardinalidade.
3. **Agrupar por setores de mercado inferidos da descrição:** rejeitada por ausência de fonte oficial.
4. **Contar especificações em vez de códigos distintos:** rejeitada por inflar percentuais quando
   várias especificações compartilham o mesmo cClassTrib.

## Critérios de revisão

Revisar se surgirem anotações humanas de cobertura que não pertençam a especificações, integração
externa de pesquisa normativa ou necessidade de snapshots históricos independentes do catálogo.
