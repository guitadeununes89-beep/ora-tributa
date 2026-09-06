# RT-IBSCBS-0009 — relatório de divergência de referência jurídica

- **Data da revisão inicial:** 2026-09-02
- **Revalidação de fechamento:** 2026-09-03
- **Resultado permitido alcançado:** `BLOCKED_LEGAL_REFERENCE_CONFLICT`
- **Status documental:** `DRAFT`
- **CST / cClassTrib analisados:** `200` / `200024`

## Comparação literal das fontes oficiais

| Fonte | Dispositivo | Texto relevante | Conclusão |
|---|---|---|---|
| Tabela oficial cClassTrib publicada em 23/06/2026, IT 2025.002 v1.60 | linha `200024`; fundamento `Art. 463` | descreve o destinatário como habilitado “nos termos do art. 456” | CONFLITO: a própria linha combina art. 463 com uma remissão incompatível com o inciso I desse artigo. |
| LC nº 214/2025 original | art. 463, I → art. 460 | exige contribuinte habilitado nos termos do art. 460 | Não sustenta a remissão ao art. 456. |
| LC nº 214/2025 compilada vigente | art. 463, I → art. 460 | mantém a habilitação pelo art. 460; o art. 456 trata de tema distinto | Confirma a cadeia 463 → 460. |
| LC nº 227/2026 | art. 460, I e II | detalha as modalidades de habilitação | Não renumera o art. 463 e não troca sua remissão para o art. 456. |
| Resolução CGIBS nº 6/2026 | arts. 438 e 527 | o art. 527 regulamenta o art. 463 e exige habilitação do art. 438, contraparte regulamentar do art. 460 | Reforça a cadeia legal; não tem função de retificar o catálogo. |
| Resolução CGIBS nº 6/2026 | art. 527, §§ 2º, 5º a 7º; arts. 551 a 553 | inscrição Suframa, comprovação de ingresso e controle de prazo | Confirma fatos probatórios, sem sanar a remissão. |
| Portal NF-e revalidado em 03/09/2026 | catálogo de 23/06/2026 e IT 2025.002 v1.60 continuam indicados como vigentes | não apresenta nova versão ou retificação do `200024` | O conflito permanece na fonte técnica oficial vigente. |
| Índice oficial de resoluções do CGIBS revalidado em 03/09/2026 | Resolução nº 6/2026 permanece o Regulamento do IBS | não foi identificado ato posterior listado que retifique a remissão do catálogo | Ausência de correção oficial localizada; não autoriza correção por interpretação. |

## Temporalidade

- `effective_from`: **2026-01-01**, por enquadramento nas demais disposições do art. 544, VI;
- `effective_to`: aberto;
- versão legal: LC nº 214/2025 compilada com alterações da LC nº 227/2026;
- versão do catálogo: `2026-06-23`, ID `2295b90f-2f92-4fa4-8181-3007f02b1679`;
- fingerprint do artefato oficial: `1448cb63b57d56c728da36ae7091ad2581b57fc8e364b2069c941c2009c654`.

## Conclusão

Há convergência entre lei original, lei compilada, LC nº 227/2026 e regulamento do IBS em torno da
habilitação derivada do art. 460. Há divergência literal na descrição oficial do cClassTrib `200024`,
que cita o art. 456. A plataforma não escolherá uma referência por semelhança textual.

Na revalidação de 03/09/2026, o Portal NF-e ainda apresenta a versão de 23/06/2026 como vigente e
nenhum ato oficial localizado resolveu a divergência. Até que exista correção, retificação ou
confirmação oficial inequívoca do catálogo:

- a especificação permanece `DRAFT`;
- seu resultado documental é `NECESSITA_VALIDACAO`;
- nenhum teste pode autorizar resultado conclusivo `200024`;
- nenhuma TaxRuleVersion ou publicação é permitida.

## Fontes oficiais

- LC nº 214/2025 compilada: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm
- LC nº 227/2026: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm
- Resolução CGIBS nº 6/2026: https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf
- Catálogo e IT no Portal NF-e: https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=/NJarYc9nus=
