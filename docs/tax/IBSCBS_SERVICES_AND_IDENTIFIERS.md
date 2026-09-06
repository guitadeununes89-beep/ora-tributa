# Serviços, NBS e objetos tributários

## Estado atual

`FactSet` já representa `nbs`, `ncm`, tipo de operação, origem/destino, regime, destinatário e
atributos extensíveis. Nenhum desses fatos conclui tributação sozinho. O cadastro `Product` é
versionado e não contém lógica de medicamentos, mas ainda não é o modelo final para serviços e
direitos.

## Evolução prevista

- introduzir objeto tributário tipado para bem, serviço, direito e outras naturezas aprovadas;
- manter identificadores normativos em coleção temporal, com fonte e evidência;
- adicionar NBS oficial somente por carga governada e catálogo versionado;
- separar natureza do objeto, descrição comercial, identificador normativo e fatos da operação;
- preservar casos híbridos e múltiplos candidatos como incerteza rastreável;
- tratar imóveis, finanças, importações, exportações e entes públicos em especificações próprias.

O ADR-0019 registra a decisão. Esta etapa não altera schema nem cria regra de serviços.
