# ADR-0020 — Visão de cobertura por família e entrada por objeto tributável

- **Estado:** Aceito
- **Data:** 2026-09-01
- **Relacionados:** ADR-0013, ADR-0018 e ADR-0019

## Contexto

A Etapa 9 precisa mostrar a cobertura nacional por família, preparar a consulta para diferentes tipos
de objeto e iniciar um bloco P1 sem transformar o catálogo oficial em regras. A API existente expõe
itens e métricas nacionais, mas não apresenta a agregação por família. O frontend ainda inicia a
consulta diretamente pelo cadastro `Product`.

Também é necessário preservar duas diferenças fundamentais: um cClassTrib não é uma regra e uma
família oficial do catálogo não é, por si, uma família jurídica executável. Várias regras podem chegar
ao mesmo código e uma regra pode exigir fatos que não pertencem ao cadastro do objeto.

## Decisão

1. A API de cobertura acrescentará uma projeção `families`, derivada exclusivamente do indicador
   oficial `Tipo de Alíquota` do snapshot `PUBLISHED`. As URLs e os itens existentes serão mantidos.
2. Cada família apresentará total de cClassTrib, fundamentos mapeados, códigos em `DRAFT`, aprovados,
   publicados, bloqueados e cobertura executável. As contagens são por código distinto; não implicam
   cardinalidade 1:1 entre cClassTrib, especificação e TaxRule.
3. O agrupamento oficial será exibido com seu nome de catálogo. Subfamílias jurídicas usadas para
   industrialização serão documentadas separadamente e nunca inferidas de setor comercial.
4. A primeira subfamília P1 será **operações com bens na Zona Franca de Manaus e em Áreas de Livre
   Comércio**, limitada aos cClassTrib `200022`, `200023` e `200024`. Ela permanece documental e
   `DRAFT` nesta etapa.
5. A consulta exibirá um seletor preparatório de tipo de objeto. Apenas `Produto/Mercadoria` continuará
   habilitado; serviço, direito, operação, importação, exportação e imóvel serão estados de interface
   sem rota, payload ou comportamento tributário novo.
6. `Product`, `FactSet`, persistência e tax-engine não serão alterados. A futura habilitação de objeto
   diferente de bem dependerá da evolução prevista no ADR-0019, com migração e contrato próprios.
7. Links administrativos serão filtrados pelas permissões retornadas por `/auth/me`: curadoria exige
   uma permissão de curar, aprovar ou publicar; usuários e papéis exige `MANAGE_MEMBERSHIP`.
8. O cabeçalho reservará posições para organização, empresa, estabelecimento, usuário e perfil. Onde
   ainda não houver seleção governada, mostrará somente marcador neutro, sem inventar dado.

## Consequências

- a cobertura por família continua reproduzível a partir das fontes governadas;
- o contrato da API cresce de forma aditiva e mantém compatibilidade com consumidores atuais;
- a interface deixa visível o denominador nacional e a cobertura executável de `1/164`;
- três especificações novas podem permanecer `DRAFT` sem criar TaxRuleVersion ou ruleset;
- a divergência entre a descrição oficial de `200024` e o texto legal será bloqueador explícito;
- tipos de objeto futuros não serão confundidos com funcionalidades executáveis.

## Alternativas consideradas

1. **Criar tabela editável de famílias:** rejeitada por duplicar uma projeção derivável do catálogo.
2. **Criar uma regra para cada cClassTrib:** rejeitada por incorreção jurídica e cardinalidade.
3. **Migrar `Product` para `TaxObject` nesta etapa:** rejeitada porque o bloco selecionado trata de
   bens e não justifica mudança de domínio.
4. **Criar rotas vazias para todos os tipos de objeto:** rejeitada por sugerir capacidade inexistente.

## Critérios de revisão

Revisar este ADR quando um objeto diferente de bem for habilitado, quando houver curadoria persistida
de famílias jurídicas ou quando o catálogo oficial alterar o indicador usado no agrupamento.
