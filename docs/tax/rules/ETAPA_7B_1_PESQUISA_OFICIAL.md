# Etapa 7B.1 — pesquisa oficial para saneamento

## Escopo e método

Pesquisa realizada em 30/08/2026 exclusivamente em fontes oficiais, limitada aos pontos exigidos
pela revisão jurídica humana. Nenhum resultado desta pesquisa é regra executável.

## Redação histórica do art. 146

A publicação original da LC nº 214/2025 confirma que:

- o caput relacionava a alíquota zero aos medicamentos do Anexo XIV, com NCM/SH;
- o § 1º separava aquisição pública e aquisição por entidade de saúde imune com CEBAS e requisito
  relacionado ao SUS;
- o § 2º abrangia as composições do Anexo VI nas aquisições qualificadas;
- o § 3º previa eventual revisão anual do Anexo XIV;
- o § 4º tratava de inclusão temporária por emergência.

Fonte: [LC nº 214/2025 — publicação original, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-publicacaooriginal-174141-pl.html).

A LC nº 227/2026 substituiu essa redação com efeitos desde sua publicação em 14/01/2026. Portanto,
`RT-IBSCBS-0004` usa `effective_to = 2026-01-14` como fim exclusivo, representando o último dia
material de vigência em 13/01/2026.

Fonte: [LC nº 227/2026, Planalto](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm).

## Catálogos oficiais consultados

O [Portal Nacional da NF-e](https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=%2FNJarYc9nus%3D)
mantém versões históricas do catálogo cClassTrib. A versão publicada em 15/12/2025 foi consultada
diretamente pelo link oficial e registra:

- CST `200`;
- cClassTrib `200009`;
- nome relacionado ao fornecimento de medicamentos do Anexo XIV;
- referência ao art. 146 original.

Na versão publicada em 28/01/2026 e no artefato oficial local de 23/06/2026:

- o caput atual usa CST `200` e cClassTrib `200009`;
- os incisos I e II do § 1º compartilham CST `200` e cClassTrib `200010`;
- soros ou vacinas usam CST `200` e cClassTrib `200053`;
- o § 2º usa CST `200` e cClassTrib `200011`;
- o § 4º usa CST `200` e cClassTrib `200012`.

Essas correspondências não combinam fundamentos jurídicos distintos e não substituem a avaliação
dos demais fatos legais.

## Lista do art. 146, § 3º

Foram consultados o texto compilado da LC nº 214/2025, a LC nº 227/2026, o Decreto nº 12.955/2026,
o portal do Ministério da Fazenda, o Diário Oficial da União e o sítio oficial do CGIBS. O decreto e
a regulamentação do CGIBS reproduzem o dever de divulgação periódica, mas não foi localizado com
segurança, até a data da pesquisa, ato conjunto vigente que contenha a lista exigida pelo § 3º.

Fontes normativas consultadas:

- [LC nº 214/2025 compilada, Planalto](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm);
- [Decreto nº 12.955/2026, Planalto](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm);
- [Resolução CGIBS nº 6/2026](https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf).

Conclusão conservadora: manter `NEEDS_ART146_PAR3_OFFICIAL_LIST`, não inferir lista e não remover a
condição das especificações afetadas.

## Vínculos governados

Os marcadores de fonte e catálogo não foram substituídos. O repositório contém o artefato normativo
e seu manifesto, mas não contém exportação dos IDs persistidos; o PostgreSQL local e o backend não
estavam disponíveis para consulta. Criar IDs manualmente violaria a orientação recebida.

O catálogo histórico de 15/12/2025 foi usado somente para confirmação documental. Ele ainda não é
um snapshot governado `PUBLISHED` da plataforma.
