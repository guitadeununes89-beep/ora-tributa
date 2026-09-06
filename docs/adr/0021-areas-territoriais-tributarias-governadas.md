# ADR-0021 — Áreas territoriais tributárias governadas

- **Estado:** Aceito
- **Data:** 2026-09-02
- **Relacionados:** ADR-0007, ADR-0009, ADR-0013, ADR-0019 e ADR-0020

## Contexto

Os tratamentos dos arts. 445, 448 e 463 da Lei Complementar nº 214/2025 dependem de recortes
territoriais específicos. UF, município textual ou CEP isolado não provam que um estabelecimento ou
entrega esteja dentro do perímetro legal. Codificar listas municipais dentro de regras Python criaria
fonte paralela sem versão, vigência ou prova.

## Decisão

1. O domínio futuro adotará `TaxJurisdictionArea`, ou equivalente, como referência territorial
   governada e independente de `Product`.
2. Cada versão registrará identificador estável, tipo (`ZFM`, `ALC` ou outro), nome oficial, fonte,
   dispositivo, vigência jurídica, tempo de registro, versão, estado e fingerprint.
3. Limites, municípios parcialmente abrangidos e critérios administrativos serão snapshots imutáveis.
4. Um resolvedor fora do tax-engine confrontará evidências com a versão aplicável. O motor receberá
   `area_id`, `area_version_id`, relação (`INSIDE`, `OUTSIDE`, `BOUNDARY`, `UNKNOWN`), fonte
   da evidência e data.
5. CEP, UF e município poderão auxiliar a busca, mas nunca concluir o enquadramento isoladamente.
6. Nenhuma lista municipal ou geometria será codificada em regra Python.
7. Esta etapa não cria tabela, migração, endpoint nem comportamento executável.

## Consequências

- decisões territoriais poderão ser reproduzidas conforme a vigência;
- fronteiras e evidência insuficiente resultarão em `NECESSITA_VALIDACAO`;
- a implementação futura exigirá ADR complementar e carga de fonte oficial.

## Alternativas consideradas

Inferência por UF, município ou CEP e listas embutidas foram rejeitadas por não representarem
perímetros legais versionados.

## Critérios de revisão

Revisar antes da implementação do cadastro territorial ou de suporte a geometrias e recortes
submunicipais.
