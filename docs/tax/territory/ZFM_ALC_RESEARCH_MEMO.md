# Memorando de pesquisa — Zona Franca de Manaus e Áreas de Livre Comércio

- **Status:** `PESQUISA JURÍDICA CONCLUÍDA PARA A ZFM` (fundamentação primária completa) —
  **ainda não é especificação aprovada nem dado governado**.
- **Data:** 2026-09-06 (três rodadas de pesquisa nesta data)
- **Autor:** Claude (Codex), pesquisa preparatória; **requer revisão jurídica humana** antes de
  qualquer promoção a `TaxJurisdictionAreaVersion` (ADR-0024).

> Este documento **não autoriza, por si só, carregar nenhum dado em
> `tax_jurisdiction_areas`/`tax_jurisdiction_area_versions`**. Ele existe para reduzir o trabalho da
> revisão jurídica, não para substituí-la — exatamente como os documentos `ETAPA_7B_PESQUISA_*`
> fizeram antes das especificações `RT-IBSCBS` serem submetidas à aprovação. A leitura completa da
> **Resolução CGIBS nº 6/2026** (arts. 432 a 438 e 516 a 555) elevou a confiança desta pesquisa de
> "preliminar" para "fundamentação primária completa" no caso da ZFM — mas a decisão de aprovar
> continua sendo sua.

## Objetivo

Levantar fonte oficial primária para:

1. a Zona Franca de Manaus (ZFM), necessária para implementar `RT-IBSCBS-0007` e `RT-IBSCBS-0008`
   (ambas já aprovadas juridicamente, bloqueadas apenas por falta deste território governado);
2. as Áreas de Livre Comércio (ALC), relevantes para `RT-IBSCBS-0009` (art. 463 da LC nº 214/2025,
   hoje bloqueada por outro motivo — divergência de referência — e para cobertura futura do
   catálogo).

## Zona Franca de Manaus (ZFM) — achado principal

**Definição oficial e vigente, direto da fonte primária mais recente e operacional (Resolução
CGIBS nº 6/2026, art. 433, I, que corresponde ao art. 440, I, da LC nº 214/2025):**

> "Zona Franca de Manaus: a área definida e demarcada nos termos do art. 2º do Decreto-Lei nº 288,
> de 28 de fevereiro de 1967, regulamentado pelo art. 2º do Decreto nº 61.244, de 28 de agosto de
> 1967, **compreendendo parte dos Municípios de Manaus, Rio Preto da Eva e Itacoatiara**."

Isso é uma citação **literal**, extraída do PDF oficial do CGIBS
(<https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf>),
convertido para texto com `pypdf` nesta sessão. **Resolve, com fonte primária direta, a incerteza
municipal que as duas versões anteriores deste memorando haviam deixado em aberto.**

### Cadeia normativa completa

| Camada | Norma | Conteúdo |
|---|---|---|
| Criação/demarcação original | Decreto-Lei nº 288, de 28/02/1967, art. 2º | Área contínua ≥ 10.000 km², margem esquerda dos rios Negro e Amazonas, incluindo Manaus; até 50 km a jusante e 70 km a montante. § 3º permite ao Executivo alterar a configuração por decreto. |
| Regulamentação | Decreto nº 61.244, de 28/08/1967, art. 2º | Regulamenta a demarcação do DL 288/1967. |
| Vigência | ADCT, art. 92-A (inserido pela EC nº 83/2014) | Estende os benefícios até **2073**. |
| Incorporação pela Reforma Tributária | LC nº 214/2025, arts. 439-451 ("Capítulo — Da Zona Franca de Manaus") | Não redefine a ZFM; usa o conceito acima. Art. 439 e art. 67, § 3º, II remetem ao DL 288/1967 e ao art. 92-A do ADCT. |
| Regulamento operacional do IBS | Resolução CGIBS nº 6/2026, arts. 432-438 e 516-555 | **Confirma a definição municipal citada acima** (art. 433, I) e detalha habilitação, alíquota zero, internamento e desinternamento. |

### Habilitação aos incentivos (art. 435 da Resolução = art. 442 da LC nº 214/2025)

- Inciso I: inscrição específica em cadastro da Suframa (atividade comercial/serviços/industrial
  não incentivada).
- Inciso II: inscrição específica + aprovação de projeto técnico-econômico pelo Conselho de
  Administração da Suframa (indústria incentivada), com base no processo produtivo básico.
- §§ 6º-8º: a inscrição Suframa ativa e os projetos técnico-econômicos aprovados permanecem
  válidos para fins do IBS; a Suframa deve comunicar às administrações tributárias bloqueio,
  suspensão ou cancelamento da inscrição, com efeito direto sobre a fruição do incentivo.
- **Conclusão para o resolvedor (ADR-0024):** a habilitação é um **fato registral** (cadastro
  Suframa), não geográfico. Isso já era a premissa do `application/territory.py` — **nenhuma
  mudança de arquitetura é necessária**.

### Alíquota zero — ZFM (art. 516 da Resolução = art. 445 da LC nº 214/2025; fundamenta `RT-IBSCBS-0007`)

Texto integral lido (não apenas resumo). Condições e prazos confirmados literalmente:

- Aplica-se a bem material industrializado de origem nacional, de fora da ZFM (inclusive de ALC)
  para contribuinte na ZFM habilitado (art. 435) e no regime regular ou Simples Nacional.
- § 2º: documento fiscal deve conter a inscrição Suframa do destinatário em campo específico.
- § 3º: estende-se a bens estrangeiros nacionalizados com similar nacional sujeito ao mesmo
  benefício e origem em país com acordo de igualdade de tratamento — **não** é extensão genérica,
  tem três condições cumulativas.
- § 5º: controles de ingresso são feitos pelas administrações tributárias estadual/municipais da
  ZFM e pela Suframa.
- §§ 6º-7º: **prazo de 120 dias** (prorrogável a **210 dias**, mediante requerimento justificado à
  Suframa antes do vencimento) para comprovar o internamento; sem isso, o fornecedor declara o IBS
  que seria devido (evento fiscal de não internamento).
- § 8º: aplica-se também à industrialização por encomenda.

### Internamento (arts. 551-553 da Resolução)

- Art. 551: formalização em sistema eletrônico da Suframa, conforme ato conjunto Suframa/CGIBS.
- Art. 552: internamento **não** se comprova quando o bem não ingressou fisicamente, o documento
  fiscal não foi desembaraçado, o prazo de 120 dias (sem prorrogação) foi descumprido, houve
  descumprimento processual, ou houve vício/simulação/fraude.
- Art. 553: comprovação é o registro, pela Suframa, do evento fiscal de internamento, condicionado
  ao desembaraço estadual/municipal no mesmo documento.
- Art. 554 (achado adicional, fora do escopo de 0007/0008 mas relevante para o motor futuro):
  **desinternamento** — revenda/transferência para fora da área em até 5 anos do internamento
  obriga estorno do crédito presumido; locação, comodato, doação, arrendamento também configuram
  desinternamento; industrialização por encomenda, demonstração/exposição, conserto e afins **não**
  configuram, se o retorno ocorrer em até 180 dias.

### Ainda não confirmado (para a ZFM)

- **A proposta de ampliar a ZFM às 12/13 cidades da Região Metropolitana de Manaus está em
  tramitação legislativa, não em vigor** (confirmado via notícia da Câmara dos Deputados,
  aguardando análise de outras comissões). A definição vigente continua sendo a de "parte de
  Manaus, Rio Preto da Eva e Itacoatiara" citada acima.
- Não obtive o texto integral e atualizado (redação compilada) do próprio DL nº 288/1967 — apenas
  os artigos 1º, 2º e 42 via busca externa (ele não está entre os artefatos normativos já ingeridos
  pela plataforma; apenas LC nº 214/2025, LC nº 187/2021 e LC nº 227/2026 estão). Isso não impede a
  especificação, já que a Resolução CGIBS nº 6/2026 (fonte de 2026, mais recente e diretamente
  aplicável ao IBS) já fornece a definição operacional citada acima.

## Áreas de Livre Comércio (ALC) — lista oficial confirmada

**Fonte primária:** Resolução CGIBS nº 6/2026, art. 437 (= art. 459 da LC nº 214/2025), lida
integralmente — não apenas resumo de busca:

| ALC | UF | Lei de criação | Decreto regulamentador |
|---|---|---|---|
| Tabatinga | AM | Lei nº 7.965, de 22/12/1989 | — (nenhum citado no art. 437) |
| Guajará-Mirim | RO | Lei nº 8.210, de 19/07/1991 | Decreto nº 843, de 23/06/1993 |
| Boa Vista e Bonfim | RR | Lei nº 8.256, de 25/11/1991 | Decreto nº 6.614, de 23/10/2008 |
| Macapá e Santana | AP | Lei nº 8.387/1991, art. 11 | Decreto nº 517, de 08/05/1992 |
| Brasiléia (com extensão a Epitaciolândia) e Cruzeiro do Sul | AC | Lei nº 8.857, de 08/03/1994 | Decreto nº 1.357, de 30/12/1994 |

Habilitação (art. 438 da Resolução = art. 460 da LC nº 214/2025) segue o mesmo modelo registral da
ZFM (cadastro Suframa + projeto técnico-econômico quando indústria incentivada), com um critério
adicional específico das ALC: preponderância de matéria-prima de origem regional (animal, vegetal,
mineral exceto Capítulo 26 da NCM/SH, ou agrossilvopastoril). Alíquota zero para operação com bem
industrializado nacional destinado a contribuinte habilitado em ALC segue o mesmo desenho do art.
516 (prazo de 120/210 dias, condicionantes de extensão a bem estrangeiro etc.), no art. 527 da
Resolução (= art. 463 da LC nº 214/2025 — **o mesmo dispositivo que fundamenta, e hoje bloqueia,
`RT-IBSCBS-0009`**; este achado não resolve aquele bloqueio, que é uma divergência de referência
sobre o art. 456 vs. 460, não uma questão territorial).

### Ainda não confirmado (para as ALC)

- **A relação oficial do art. 437 lista apenas os municípios-sede de cada ALC** (ex.: Brasiléia,
  Epitaciolândia, Cruzeiro do Sul), **sem mencionar** Acrelândia, Assis Brasil, Capixaba, Plácido de
  Castro, Xapuri, Feijó, Jordão, Mâncio Lima ou outros citados por reportagens. A notícia da Câmara
  "Comissão amplia municípios participantes de áreas de livre comércio do Acre" sugere um projeto
  de lei específico para essa ampliação, **ainda não identificado nem confirmado como norma
  vigente**. Para os fins de `RT-IBSCBS-0009` (que trata apenas de ALC em geral, sem uma ALC
  específica nomeada na especificação lida anteriormente), isso não é bloqueante hoje.
- Não li o texto integral das cinco leis de criação de ALC (apenas ementas e o art. 437 da
  Resolução, que já supre a necessidade de fundamento legal + decreto regulamentador para uma
  especificação territorial básica de cada área).

## Próximos passos recomendados

1. ✅ ~~Ler texto integral da Resolução CGIBS nº 6/2026~~ — feito nesta sessão para os artigos
   relevantes à ZFM/ALC (432-438, 516-555).
2. Redigir a especificação territorial formal da ZFM
   (`docs/tax/territory/specifications/`, espelhando `docs/tax/rules/specifications/`), com
   `status: DRAFT`, para sua revisão e aprovação — próximo passo natural, ainda não executado neste
   commit.
3. Repetir para as 5 ALC, se e quando forem priorizadas (nenhuma delas desbloqueia uma regra hoje
   aprovada — apenas `RT-IBSCBS-0009`, que está bloqueada por outro motivo).
4. Somente depois da sua aprovação, carregar a primeira `TaxJurisdictionAreaVersion` real via
   CLI/seed governado (ainda a ser criado) — nunca por edição manual do banco.

## Fontes consultadas

- **Resolução CGIBS nº 6, de 30 de abril de 2026** (regulamento do IBS) — PDF oficial baixado e
  convertido a texto nesta sessão (`pypdf`, 252 páginas); artigos 432 a 438 e 516 a 555 lidos
  integralmente.
  <https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf>
- `database/normative-artifacts/legal/original/lcp214-compilado.html` — texto compilado da LC nº
  214/2025 já ingerido pela plataforma (fonte governada
  `23302183-6c92-4b34-a26d-cd272e2c1b1e`); arts. 67, § 3º, II, 439 e 442 lidos diretamente desta
  fonte local.
- [Decreto-Lei nº 288, de 28 de fevereiro de 1967 (Planalto)](https://www.planalto.gov.br/ccivil_03/decreto-lei/del0288.htm)
- [Decreto-Lei nº 288/1967 — texto publicado original (Câmara)](https://www2.camara.leg.br/legin/fed/declei/1960-1969/decreto-lei-288-28-fevereiro-1967-376805-publicacaooriginal-1-pe.html)
- [EC nº 83/2014 prorroga a Zona Franca de Manaus até 2073 (Congresso/Câmara)](https://www.camara.leg.br/noticias/438935-CONGRESSO-PROMULGA-PRORROGACAO-DA-ZONA-FRANCA-DE-MANAUS-ATE-2073)
- [Comissão aprova inclusão das 12 cidades da Grande Manaus na Zona Franca (Câmara — projeto em tramitação, não vigente)](https://www.camara.leg.br/noticias/626048-comissao-aprova-inclusao-das-12-cidades-da-grande-manaus-na-zona-franca/)
- [Lei nº 7.965, de 22 de dezembro de 1989 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/l7965.htm)
- [Lei nº 8.210, de 19 de julho de 1991 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/1989_1994/l8210.htm)
- [Lei nº 8.387, de 30 de dezembro de 1991 (Câmara, publicação original)](https://www2.camara.leg.br/legin/fed/lei/1991/lei-8387-30-dezembro-1991-365181-publicacaooriginal-1-pl.html)
- [Lei nº 8.256, de 25 de novembro de 1991 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/1989_1994/L8256.htm)
- [Lei nº 15.273, de 2025, amplia a ALC de Boa Vista incluindo Pacaraima (Planalto)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15273.htm)
- [Lei nº 8.857, de 8 de março de 1994 (Planalto)](https://www.planalto.gov.br/ccivil_03/leis/1989_1994/l8857.htm)
- [Comissão amplia municípios participantes de áreas de livre comércio do Acre (Câmara — projeto em tramitação)](https://www.camara.leg.br/noticias/546414-comissao-amplia-municipios-participantes-de-areas-de-livre-comercio-do-acre)
