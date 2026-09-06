# Etapa 7B — registro da pesquisa jurídica

## Estado e limite

Pesquisa preparatória para `RT-IBSCBS-0001` a `RT-IBSCBS-0003`. As três especificações permanecem
`DRAFT`; este documento não aprova interpretação, não cria regra executável e não substitui revisão
jurídica humana.

Não foi criado novo ADR. A etapa apenas instancia o formato e o lifecycle decididos no ADR-0015,
sem alterar fronteiras, persistência, temporalidade, contrato público ou política de cálculo.

## Fontes oficiais consultadas

- [LC nº 214/2025 — texto vigente compilado, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html);
- [LC nº 214/2025 — publicação original, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-publicacaooriginal-174141-pl.html);
- [LC nº 227/2026 — Presidência da República](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm);
- [Decreto nº 12.955/2026 — texto vigente, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/decret/2026/decreto-12955-29-abril-2026-799019-normaatualizada-pe.html), arts. 208 e 222, usado apenas como confirmação regulamentar oficial da CBS;
- catálogo oficial local `cClassTrib-2026-06-22.xlsx`, publicado em 23/06/2026, manifesto
  `database/normative-artifacts/manifests/ibscbs-cclasstrib-2026-06-23.json`, SHA-256
  `1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654`.

Não foram usados artigos, blogs ou fontes secundárias como fundamento.

## Texto vigente confirmado

### Redução de 60%

O art. 133, caput, da LC nº 214/2025 reduz em 60% as alíquotas do IBS e da CBS no fornecimento de
medicamentos registrados na Anvisa ou produzidos por farmácias de manipulação e ressalva
expressamente os medicamentos sujeitos à alíquota zero do art. 146. O § 1º alcança composições
específicas do Anexo VI. O § 2º condiciona a aplicação aos medicamentos industrializados ou
importados por pessoas jurídicas com compromisso de ajustamento de conduta com a União e o CGIBS
ou que cumpram a sistemática CMED, na forma da lei.

O art. 544, VI, atribui efeitos aos demais dispositivos a partir de 01/01/2026. A Etapa 7B limita
`RT-IBSCBS-0001` a medicamento registrado industrializado ou importado; farmácia de manipulação e
composições do Anexo VI exigirão especificações próprias.

### Alíquota zero por destinação sanitária

O art. 146, na redação dada pelo art. 174 da LC nº 227/2026, exige medicamento registrado na Anvisa
e destinação, de acordo com o registro sanitário, a: doenças raras; doenças negligenciadas;
oncologia; diabetes; HIV/aids e outras IST; doenças cardiovasculares; ou Programa Farmácia Popular
do Brasil ou equivalente. O § 3º prevê lista divulgada a cada 120 dias. A LC nº 227/2026 foi
publicada no DOU de 14/01/2026 e seu art. 182, III, atribui efeitos aos demais dispositivos desde a
publicação.

`RT-IBSCBS-0002` começa em 14/01/2026. A revisão humana deverá decidir se a lista do § 3º é requisito
constitutivo ou instrumento de divulgação; até lá o DRAFT exige confirmação de inclusão e impede
conclusão silenciosa.

### Alíquota zero por aquisição pública

O art. 146, § 1º, I, na redação vigente, alcança medicamentos registrados na Anvisa adquiridos por
órgãos da administração pública direta, autarquias ou fundações públicas. A hipótese já constava do
§ 1º, I, da publicação original e produz efeitos desde 01/01/2026. A LC nº 227/2026 reestruturou o
artigo com efeitos desde 14/01/2026, mas manteve esses três adquirentes.

`RT-IBSCBS-0003` exige prova da natureza jurídica e de que o ente é o adquirente efetivo. CNPJ ou
nome, isoladamente, não são suficientes.

## Histórico preservado

De 01/01/2026 a 13/01/2026, o caput original do art. 146 reduzia a zero as alíquotas para os
medicamentos relacionados no Anexo XIV com suas classificações NCM/SH. O § 1º, I, já previa a
aquisição pública. A partir de 14/01/2026, a LC nº 227/2026 substituiu o caput pela enumeração de
destinações sanitárias e revogou o Anexo XIV. Nenhuma das especificações apaga esse predecessor:

- `RT-IBSCBS-0001` exige seleção temporal da versão do art. 146 ao avaliar a ressalva;
- `RT-IBSCBS-0002` cobre apenas a redação nova a partir de 14/01/2026;
- `RT-IBSCBS-0003` registra a continuidade da hipótese pública nas duas redações.

## Taxonomia oficial

O cruzamento foi feito pelas referências legais e descrições integrais do catálogo, no mesmo
snapshot, sem inferência por memória ou mera semelhança:

| Regra | CST | cClassTrib | Linha oficial correspondente |
|---|---:|---:|---|
| RT-IBSCBS-0001 | 200 | 200032 | Medicamentos registrados na Anvisa ou produzidos por farmácias de manipulação, ressalvada alíquota zero; art. 133 |
| RT-IBSCBS-0002 | 200 | 200009 | Medicamentos registrados na Anvisa; art. 146 |
| RT-IBSCBS-0003 | 200 | 200010 | Medicamentos registrados na Anvisa adquiridos por órgãos da administração pública; art. 146, § 1º, I e II |

O ID de banco do snapshot `PUBLISHED` não pôde ser consultado nesta execução. Os JSONs usam marcador
explícito `PENDING-PUBLISHED-CATALOG-1448CB63A41B`; ele deve ser substituído pelo ID governado após
conferência no tenant e, até lá, deve manter o preflight em `NOT_READY`. Em `RT-IBSCBS-0003`, a
cClassTrib oficial também menciona entidades imunes do inciso II, embora o escopo do DRAFT seja
apenas o inciso I; a adequação desse recorte requer validação humana.

## Decisões que dependem de revisão humana

- autoria, revisão, aprovação e evidência de aprovação;
- cadastro/vínculo da fonte oficial no tenant;
- vínculo do ID persistido do snapshot oficial publicado;
- caráter da lista do art. 146, § 3º, para `RT-IBSCBS-0002` e identificação do ato temporal aplicável;
- suficiência probatória da condição do art. 133, § 2º;
- vocabulário canônico das destinações sanitárias e das naturezas jurídicas;
- adequação da cClassTrib `200010` ao recorte exclusivo do art. 146, § 1º, I.
