# Especificações territoriais governadas

Este diretório governa a preparação documental de áreas territoriais tributárias (ADR-0021,
ADR-0024): Zona Franca de Manaus (ZFM) e Áreas de Livre Comércio (ALC). Todas as seis
especificações abaixo estão `DRAFT` e **nenhuma foi aprovada**. Nenhuma autoriza carregar dado em
`tax_jurisdiction_areas`/`tax_jurisdiction_area_versions`.

## Artefatos

- `TJA-ZFM.json`: Zona Franca de Manaus — fundamentação primária mais completa (Resolução CGIBS
  nº 6/2026 lida na íntegra para os artigos relevantes); necessária para `RT-IBSCBS-0007` e
  `RT-IBSCBS-0008` (já aprovadas juridicamente, bloqueadas apenas por este território);
- `TJA-ALC-TABATINGA.json`, `TJA-ALC-GUAJARA-MIRIM.json`, `TJA-ALC-BOA-VISTA-BONFIM.json`,
  `TJA-ALC-MACAPA-SANTANA.json`, `TJA-ALC-BRASILEIA-CRUZEIRO-DO-SUL.json`: as cinco Áreas de Livre
  Comércio oficiais, confirmadas via art. 437 da Resolução CGIBS nº 6/2026 (lei de criação e
  decreto regulamentador de cada uma); nenhuma lei de ALC individual foi lida na íntegra — apenas
  ementas e o próprio art. 437. Relevantes para `RT-IBSCBS-0009` (hoje bloqueada por outro motivo:
  divergência de referência entre art. 456 e art. 460) e para cobertura futura;
- `../ZFM_ALC_RESEARCH_MEMO.md`: memorando de pesquisa com o histórico completo, fontes
  consultadas e todas as incertezas registradas por área.

## Diferenças em relação a `docs/tax/rules/specifications/`

Não existe ainda um pre-flight automatizado (`validate-tax-rule-spec` equivalente) para
especificações territoriais — isso é trabalho futuro, não decidido nesta etapa. A revisão hoje é
inteiramente manual: leitura humana do `legal_foundation`, do `criteria` e, principalmente, de
`known_conflicts`, que documenta explicitamente cada ressalva (fonte não lida na íntegra, disputa
sobre municípios adicionais, proposta legislativa não vigente etc.).

## Fluxo (mesmo espírito de `RT-IBSCBS`, adaptado)

```text
Pesquisa de fonte oficial (ZFM_ALC_RESEARCH_MEMO.md)
  → especificação territorial DRAFT (este diretório)
  → revisão jurídica humana (você, mesma capacidade usada em RT-IBSCBS-0003)
  → aprovação (status → APPROVED, campos de approval preenchidos)
  → carga governada real (CLI/seed ainda não criado — ADR-0024 não autorizou esta etapa)
  → tax_jurisdiction_areas / tax_jurisdiction_area_versions
```

## Proibições

- não carregar nenhuma destas especificações em banco sem aprovação registrada;
- não presumir municípios adicionais além dos citados literalmente no art. 437 da Resolução CGIBS
  nº 6/2026 (ou em lei/decreto individual, quando lido na íntegra);
- não confundir `known_conflicts` com bloqueio jurídico definitivo — cada item é uma ressalva de
  pesquisa, a ser resolvida ou aceita explicitamente na aprovação;
- não tratar habilitação/registro Suframa (fato registral) como parte destas especificações
  territoriais — é um fato separado, já previsto nas próprias especificações `RT-IBSCBS-0007`/
  `0008`/`0009`.
