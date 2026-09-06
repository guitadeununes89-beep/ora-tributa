# Plano de tabelas oficiais complementares IBS/CBS

## Princípio

Tabela técnica publicada não equivale a tratamento tributário. Cada artefato deve passar por
manifesto, preservação do original, hash, staging, validação, revisão, aprovação, publicação e diff
histórico antes de ser referenciado por regra aprovada.

## Estados do inventário

- `INGESTED`: artefato oficial preservado, versionado e persistido pelo pipeline governado;
- `AVAILABLE_NOT_INGESTED`: artefato oficial identificado de forma verificável, ainda fora do
  pipeline local;
- `REQUIRES_ANALYSIS`: fonte, autoridade, estrutura ou aplicabilidade ainda precisa ser confirmada.

| Artefato | Estado atual | Finalidade técnica | Fonte oficial exigida | Gate antes de uso no motor |
|---|---|---|---|---|
| CST/cClassTrib IBS/CBS | `INGESTED` | classificação técnica oficial | Portal NF-e, snapshot 2026-06-23 | catálogo já publicado; descrição não vira regra |
| cCredPres IBS/CBS | `REQUIRES_ANALYSIS` | códigos de crédito presumido | portal/documento técnico oficial | catálogo publicado + especificação de crédito aprovada |
| alíquotas CBS/IBS | `REQUIRES_ANALYSIS` | valores por período e hipótese | ato normativo e tabela oficial competente | modelo decimal, vigência e arredondamento aprovados |
| índice de biocombustível | `REQUIRES_ANALYSIS` | parâmetro técnico de operações monofásicas | órgão oficial competente | versão temporal + regra jurídica específica |
| meios de pagamento | `REQUIRES_ANALYSIS` | códigos técnicos para documentos e split payment | especificação técnica oficial | governança de catálogo; sem inferir incidência |
| anexos e listas legais | `REQUIRES_ANALYSIS` | produtos, serviços ou operações enumerados | ato oficial e versão histórica | vínculo linha–dispositivo e evidência temporal |
| NBS e tabelas de serviços | `REQUIRES_ANALYSIS` | identificador auxiliar de serviços | fonte oficial da nomenclatura | identificadores versionados; NBS nunca conclusiva isoladamente |

Nenhuma tabela complementar possui manifesto e artefato local suficientes para receber
`AVAILABLE_NOT_INGESTED` nesta revisão. O estado só deve ser promovido quando URL, autoridade,
versão e hash esperado puderem ser registrados sem inferência.

## Modelo proposto

Reutilizar o lifecycle de catálogos do ADR-0013. Cada família terá identidade estável, snapshots
imutáveis, fonte legal/técnica, hash, contagens, relatório de importação e eventos. Relações com
regras serão explícitas e muitos-para-muitos quando a norma exigir.
