# ADR-0019 — Objetos tributários e identificadores extensíveis

- **Estado:** Aceito
- **Data:** 2026-09-01
- **Relacionados:** ADR-0001, ADR-0008, ADR-0014 e ADR-0018

## Contexto

`FactSet` já admite NCM, NBS, tipo de operação e atributos extensíveis. O cadastro `Product` não é
específico de medicamentos, mas seu nome e identificadores iniciais refletem bens. A cobertura
nacional futura inclui serviços, direitos, imóveis, finanças, importação e exportação.

## Decisão

1. O motor continuará recebendo `FactSet` genérico; nenhum campo sanitário será promovido a
   requisito global.
2. NCM, NBS e identificadores futuros serão evidências tipadas e versionadas, nunca decisão fiscal.
3. Uma evolução posterior introduzirá um conceito de objeto tributário (`TaxObject`) ou camada
   equivalente, com tipo `GOOD`, `SERVICE`, `RIGHT` ou outro valor governado e coleção temporal de
   identificadores normativos.
4. O modelo atual `Product` será preservado nesta etapa para evitar migração sem caso de uso
   aprovado. A interface pode denominá-lo “Produtos e serviços”, deixando a limitação explícita.
5. Regras para serviços, direitos ou regimes específicos só serão criadas após especificação
   jurídica própria; não serão inferidas por NBS, descrição ou tipo do objeto.

## Consequências

- a RT-IBSCBS-0003 permanece isolada em atributos específicos da regra;
- não há migração ou regra nova na Etapa 8;
- NBS já pode participar de `FactSet`, mas cadastro, fonte e validação temporal ainda exigem etapa
  própria;
- importações/exportações e partes da operação continuam fatos, não categorias de regra.

## Alternativas consideradas

- renomear imediatamente todas as tabelas `Product`: rejeitada sem migração e casos de uso;
- adicionar dezenas de colunas setoriais: rejeitada por acoplamento;
- usar apenas descrição/NCM/NBS: rejeitada por insuficiência jurídica.
