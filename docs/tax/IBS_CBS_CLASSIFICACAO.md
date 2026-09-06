# Catálogo oficial CST IBS/CBS e cClassTrib

## Escopo desta entrega

Esta etapa introduz o primeiro conteúdo normativo real do projeto como **catálogo consultivo,
versionado e governado**. Ela não cria uma regra executável e não determina CST ou cClassTrib de
produto, NCM, serviço ou operação.

O conteúdo aceito é exclusivamente a planilha “Tabela de Classificação Tributária do IBS e CBS”
disponibilizada pelo Portal Nacional da NF-e/ENCAT em 23/06/2026, associada ao Informe Técnico
2025.002 v1.60. A consulta da fonte foi realizada em 29/08/2026.

## CST, cClassTrib e relacionamento

Nesta implementação, `CST-IBS/CBS` é preservado como o código e a descrição agrupadores que a
própria planilha oficial associa às classificações. `cClassTrib` é preservado como o código mais
detalhado, seu nome, sua descrição e seus demais atributos oficiais. Cada cClassTrib referencia
obrigatoriamente um CST existente **na mesma versão** do catálogo.

Essa relação descreve a estrutura da fonte; não significa que a plataforma já saiba escolher um
desses códigos para uma mercadoria ou operação. Quando o significado de um indicador não estiver
formalmente especificado para uso executável, a plataforma apenas o exibe com sua proveniência.
## Artefato e proveniência

- artefato original: `database/normative-artifacts/original/cClassTrib-2026-06-22.xlsx`;
- manifesto: `database/normative-artifacts/manifests/ibscbs-cclasstrib-2026-06-23.json`;
- SHA-256 do original: `1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654`;
- SHA-256 da representação normalizada: `9b65c977cdd37b30f0146b10f8addd7175f11389fc08196a9dfebfd5258b2008`;
- assinatura do schema: `fb87c22952135fe428a552f32d330d2cdd132bd5aae6dfc0a33747c58a6135c6`;
- resultado reproduzível: 18 CST, 164 cClassTrib e 185 linhas de staging, sem erro.

O nome interno das abas menciona 01/06/2026, o nome do arquivo menciona 22/06/2026 e o portal
registra publicação em 23/06/2026. Os três valores são preservados; o sistema não escolhe nem
reescreve silenciosamente uma dessas datas.

## Pipeline controlado

```text
fonte oficial → original + SHA-256 → parser seguro → staging → validação estrutural
              → revisão humana → aprovação → publicação de snapshot imutável
```

Estados válidos: `IMPORTED → VALIDATED → IN_REVIEW → APPROVED → PUBLISHED`. Um erro pode levar a
`FAILED`, que é terminal. Downloads e validações nunca publicam automaticamente.

O importador:

- limita tamanhos comprimido/descomprimido e quantidade de entradas ZIP;
- rejeita caminhos ZIP inseguros e relacionamentos externos que não sejam hyperlinks HTTPS;
- reconhece somente a assinatura exata das duas tabelas oficiais;
- preserva cada linha e diagnóstico no staging;
- conserva códigos como string, inclusive zeros à esquerda;
- converte datas em ISO e números decimais em string, sem persistir `float`;
- valida campos obrigatórios, duplicidade e vínculo cClassTrib → CST no mesmo snapshot;
- calcula hashes canônicos antes de permitir avanço no lifecycle.

## Modelo persistente

O agregado possui identidade de catálogo, versões, fonte legal, staging, CST, cClassTrib e eventos
append-only. A publicação cria um snapshot: alteração oficial futura exige nova versão e diff
estruturado. Triggers PostgreSQL bloqueiam alteração ou exclusão da versão publicada e de seus
itens.

O catálogo é isolado por organização nesta fase. A API sempre recebe a organização do contexto
autenticado, nunca do corpo da requisição. Curador importa/valida/envia para revisão, aprovador
aprova e publicador publica; com segregação habilitada, essas decisões exigem atores distintos.

## Consulta e limites jurídicos

A rota de interface é `/reforma-tributaria/classificacao`. A API expõe somente snapshots
publicados nas consultas comuns, com busca literal por código/texto, filtro CST e cartão de
proveniência. O diff mostra inclusões, remoções e alterações de campos sem afirmar seu efeito
jurídico.

Os indicadores e percentuais da planilha são preservados como atributos oficiais, mas não foram
interpretados como condições de cálculo. Não há nesta entrega:

- associação automática entre NCM/produto/operação e CST/cClassTrib;
- cálculo de IBS, CBS, créditos, reduções ou regimes monofásicos;
- Imposto Seletivo, Split Payment, medicamentos, ICMS ou PIS/COFINS;
- ingestão de XML fiscal de produção.

Qualquer uso determinístico futuro deste catálogo exige especificação jurídica própria, exemplos
positivos/negativos, vigência, dados contextuais suficientes e novo ADR quando alterar fronteiras.
