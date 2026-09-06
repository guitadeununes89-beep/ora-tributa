# Memorando de pesquisa preliminar — Zona Franca de Manaus e Áreas de Livre Comércio

- **Status:** `PESQUISA PRELIMINAR` — não é especificação aprovada nem dado governado.
- **Data:** 2026-09-06
- **Autor:** Claude (Codex), pesquisa preparatória; **requer revisão jurídica humana** antes de
  qualquer promoção a `TaxJurisdictionAreaVersion` (ADR-0024).

> Este documento **não autoriza, por si só, carregar nenhum dado em
> `tax_jurisdiction_areas`/`tax_jurisdiction_area_versions`**. Ele existe para reduzir o trabalho da
> revisão jurídica, não para substituí-la — exatamente como os documentos `ETAPA_7B_PESQUISA_*`
> fizeram antes das especificações `RT-IBSCBS` serem submetidas à aprovação.

## Objetivo

Levantar fonte oficial primária para:

1. a Zona Franca de Manaus (ZFM), necessária para implementar `RT-IBSCBS-0007` e `RT-IBSCBS-0008`
   (ambas já aprovadas juridicamente, bloqueadas apenas por falta deste território governado);
2. as Áreas de Livre Comércio (ALC), relevantes para `RT-IBSCBS-0009` (art. 463 da LC nº 214/2025,
   hoje bloqueada por outro motivo — divergência de referência — e para cobertura futura do
   catálogo).

## Zona Franca de Manaus (ZFM)

- **Fonte primária:** Decreto-Lei nº 288, de 28 de fevereiro de 1967.
  <https://www.planalto.gov.br/ccivil_03/decreto-lei/del0288.htm>
- **Definição geográfica (art. 2º, caput, e §§ 1º e 3º):** área contínua com superfície mínima de
  10.000 km², à margem esquerda dos rios Negro e Amazonas, incluindo a cidade de Manaus; até 50 km
  a jusante e 70 km a montante de Manaus nas margens dos rios. O § 3º autoriza o Poder Executivo a
  **aumentar a área originalmente estabelecida ou alterar sua configuração por decreto**.
- **Regulamentação inicial:** Decreto nº 61.244, de 28 de agosto de 1967.
- **Alteração relevante do regime:** Lei nº 8.387, de 30 de dezembro de 1991 (ajustes amplos ao
  regime fiscal e à administração pela Suframa).
- **Vigência:** prazo original de 30 anos (art. 42 do DL 288/1967), prorrogado por sucessivas
  emendas constitucionais; a mais recente é a **EC nº 83/2014**, que inseriu o art. 92-A no ADCT e
  estende os benefícios até **2073**.

### Incertezas explícitas (não resolvidas nesta pesquisa)

- Não confirmei se o Poder Executivo exerceu o poder do art. 2º, § 3º do DL 288/1967 para alterar a
  configuração original da área desde 1967, nem localizei um decreto consolidado que defina o
  perímetro atual em termos de município(s) ou coordenadas — a definição de 1967 é territorial
  (raio/distância de rios), não municipal, o que não é diretamente utilizável como "município
  abrangido" sem uma conversão documentada.
- **Não verifiquei como a LC nº 214/2025 (arts. 442, 445, 448) ou a Resolução CGIBS nº 6/2026
  definem "Zona Franca de Manaus" para fins de IBS/CBS** — se por remissão direta ao DL nº 288/1967
  ou por definição própria. Isso é essencial: a especificação `RT-IBSCBS-0007`/`0008` pode exigir um
  critério diferente do texto de 1967.
- Não obtive o texto integral e atualizado (redação compilada) do DL nº 288/1967; extraí apenas os
  artigos citados acima via busca, não uma leitura completa e literal do texto consolidado.

## Áreas de Livre Comércio (ALC)

| ALC | UF | Município(s) | Lei de criação | Regulamentação | Observação |
|---|---|---|---|---|---|
| Tabatinga | AM | Tabatinga | Lei nº 7.965/1989 | — | Área de 20 km² à margem esquerda do rio Solimões, incluindo perímetro urbano. |
| Guajará-Mirim | RO | Guajará-Mirim | Lei nº 8.210/1991 | Decreto nº 843/1993 | Área de 82,50 km² à margem direita do rio Mamoré. |
| Macapá e Santana | AP | Macapá, Santana | Lei nº 8.387/1991, art. 11 | Decreto nº 517/1992 | Área de 220 km². |
| Boa Vista e Bonfim | RR | Boa Vista, Bonfim (+ Pacaraima) | Lei nº 8.256/1991; alterada pela Lei nº 15.273/2025 (inclui Pacaraima) | — | Benefícios mantidos por 25 anos da publicação (1991). |
| Brasiléia e Cruzeiro do Sul | AC | Brasiléia, Epitaciolândia, Cruzeiro do Sul | Lei nº 8.857/1994 | — | Cada área com 20 km², perímetros urbanos dos respectivos municípios. |

### Incertezas explícitas (não resolvidas nesta pesquisa)

- Fontes secundárias (reportagens, boletins) mencionam listas **mais amplas** de municípios
  "integrantes" de cada ALC (ex.: Acrelândia, Assis Brasil, Capixaba, Plácido de Castro e Xapuri
  para a ALC de Brasiléia; Feijó, Jordão, Mâncio Lima e outros para Cruzeiro do Sul). **Não
  confirmei essas listas no texto literal da Lei nº 8.857/1994 ou de decreto regulamentador** — elas
  podem vir de atos administrativos posteriores (ex.: ampliação por comissão, citada em notícia da
  Câmara dos Deputados) que precisam ser identificados e citados individualmente, não presumidos.
- Não obtive o texto literal completo de nenhuma das cinco leis de ALC listadas acima — apenas
  resumos de busca. Antes de qualquer especificação `TaxJurisdictionAreaVersion` real, cada uma
  precisa ser lida integralmente na fonte oficial.
- Não investiguei qual(is) dessas ALCs (se alguma) correspondem à hipótese do art. 463/`RT-IBSCBS-0009`
  especificamente — a especificação 0009 permanece bloqueada por outro motivo (divergência de
  referência legal) e não depende deste levantamento para ser resolvida.

## Próximos passos recomendados (não executados aqui)

1. Ler o texto integral e consolidado do DL nº 288/1967 e confirmar com a Suframa (ou a
   regulamentação de LC nº 214/2025) a definição de "ZFM" aplicável ao IBS/CBS.
2. Ler o texto integral de cada lei de ALC, com atenção a decretos regulamentadores que fixem
   coordenadas/municípios de forma mais precisa que a lei original.
3. Somente após essa confirmação, redigir uma especificação territorial formal
   (`docs/tax/territory/specifications/`, espelhando `docs/tax/rules/specifications/`) para cada
   área, com fundamento legal completo, e submetê-la à sua revisão e aprovação — nos mesmos moldes
   de uma especificação `RT-IBSCBS`.
4. Somente depois disso, carregar a primeira `TaxJurisdictionAreaVersion` real via CLI/seed
   governado (ainda a ser criado) — nunca por edição manual do banco.

## Fontes consultadas

- [Decreto-Lei nº 288, de 28 de fevereiro de 1967 (Planalto)](https://www.planalto.gov.br/ccivil_03/decreto-lei/del0288.htm)
- [Decreto-Lei nº 288/1967 — texto publicado original (Câmara)](https://www2.camara.leg.br/legin/fed/declei/1960-1969/decreto-lei-288-28-fevereiro-1967-376805-publicacaooriginal-1-pe.html)
- [EC nº 83/2014 prorroga a Zona Franca de Manaus até 2073 (Congresso/Câmara)](https://www.camara.leg.br/noticias/438935-CONGRESSO-PROMULGA-PRORROGACAO-DA-ZONA-FRANCA-DE-MANAUS-ATE-2073)
- [Zona Franca de Manaus oficialmente prorrogada até 2073 (Suframa)](https://www.gov.br/suframa/pt-br/assuntos/noticias/zona-franca-de-manaus-esta-oficialmente-prorrogada-ate-2073)
- [Lei nº 7.965, de 22 de dezembro de 1989 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/l7965.htm)
- [Lei nº 8.210, de 19 de julho de 1991 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/1989_1994/l8210.htm)
- [Lei nº 8.387, de 30 de dezembro de 1991 (Câmara, publicação original)](https://www2.camara.leg.br/legin/fed/lei/1991/lei-8387-30-dezembro-1991-365181-publicacaooriginal-1-pl.html)
- [Lei nº 8.256, de 25 de novembro de 1991 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/1989_1994/L8256.htm)
- [Lei nº 15.273, de 2025, amplia a ALC de Boa Vista incluindo Pacaraima (Planalto)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15273.htm)
- [Lei nº 8.857, de 8 de março de 1994 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/1989_1994/l8857.htm)
- [Comissão amplia municípios participantes de áreas de livre comércio do Acre (Câmara)](https://www.camara.leg.br/noticias/546414-comissao-amplia-municipios-participantes-de-areas-de-livre-comercio-do-acre)
- [Áreas de Livre Comércio — Suframa (página institucional, consultada via busca; URL direta retornou 404 nesta pesquisa)](https://www.gov.br/suframa/pt-br/assuntos/areas-de-livre-comercio)
