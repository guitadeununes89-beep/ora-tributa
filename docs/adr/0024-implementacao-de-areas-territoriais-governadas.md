# ADR-0024 — Implementação do modelo de áreas territoriais tributárias governadas

- **Status:** Aceita
- **Data:** 2026-09-06
- **Responsáveis:** Guilherme Nunes (responsável tributário e jurídico do projeto)
- **Relacionados:** ADR-0002, ADR-0007, ADR-0009, ADR-0013, ADR-0019, ADR-0020, ADR-0021

## Contexto

O ADR-0021 decidiu adotar `TaxJurisdictionArea` como referência territorial governada para
tratamentos como os dos arts. 445, 448 e 463 da LC nº 214/2025 (Zona Franca de Manaus e Áreas de
Livre Comércio), mas explicitamente **não** criou tabela, migração, endpoint ou comportamento
executável, e exigiu um ADR complementar antes da implementação.

`RT-IBSCBS-0007` v3 e `RT-IBSCBS-0008` v3 foram aprovadas juridicamente (Etapa 9.3,
`docs/tax/ETAPA_9_3_LEGAL_APPROVAL_P1.md`), mas ambas registram o bloqueador
`NEEDS_GOVERNED_ZFM_TERRITORY_AND_OPERATIONAL_ACTS`: nenhuma delas pode ser implementada como regra
executável enquanto esse modelo não existir. Este ADR propõe o desenho técnico. Ele **não** decide
qual território real pertence à ZFM ou a qualquer ALC — isso exige pesquisa jurídica e fonte
oficial própria, tratada com o mesmo rigor de uma especificação de regra (Decreto-Lei nº 288/1967,
atos da Suframa e leis específicas de cada Área de Livre Comércio), fora do escopo desta decisão de
arquitetura.

## Decisão

1. **Identidade e versão governada**, seguindo o padrão bitemporal já usado para regras e catálogo
   (ADR-0002, ADR-0009, ADR-0013):
   - `TaxJurisdictionAreaIdentity`: identificador estável, tipo (`ZFM`, `ALC`, extensível),
     nome oficial, criado/atualizado com ator e instante.
   - `TaxJurisdictionAreaVersion`: snapshot imutável — fonte legal (`legal_source_id`),
     dispositivo específico, descrição estruturada do critério administrativo (ex.: lista de
     municípios ou subdivisões abrangidas, quando a fonte oficial as definir dessa forma),
     `valid_from`, `valid_to` (vigência jurídica), `recorded_at` (tempo de sistema), `version`,
     `status` (`DRAFT → IN_REVIEW → APPROVED → PUBLISHED → SUPERSEDED/WITHDRAWN`, reaproveitando o
     vocabulário do ADR-0006) e `content_hash`/fingerprint.
   - Publicação segue o mesmo princípio de imutabilidade e não-destrutividade de ADR-0002:
     correção ou mudança legislativa cria nova versão; nunca `UPDATE` do conteúdo publicado.
2. **Nenhuma geometria nem lista municipal é codificada em Python.** A descrição estruturada acima
   vive apenas como dado governado (linha de banco), nunca como constante ou condição embutida em
   regra do `tax-engine`, confirmando a decisão já tomada no ADR-0021.
3. **Resolvedor fora do `tax-engine`**: um serviço de aplicação (`backend`) recebe evidências (ex.:
   inscrição Suframa, CNPJ/endereço do estabelecimento, comprovantes de habilitação — os mesmos
   fatos já previstos em `RT-IBSCBS-0007`/`0008`, como `buyer.art_442_habilitation_status` e
   `operation.zfm_area_version_id`) e devolve `area_id`, `area_version_id`, relação (`INSIDE`,
   `OUTSIDE`, `BOUNDARY`, `UNKNOWN`) e a fonte da evidência. O `tax-engine` continua recebendo
   apenas esse resultado já resolvido, nunca dados brutos de endereço ou geometria.
4. **Escopo técnico da Fase 1** (esta implementação): apenas o cadastro governado
   (identidade + versão + lifecycle + persistência) e o contrato do resolvedor (porta/interface).
   **Não inclui**: geometria/poligonal, importador automático de fonte oficial, nem o preenchimento
   de dados reais de qualquer área. Carga de dados reais exige pesquisa jurídica própria (fonte
   oficial, dispositivo, vigência) revisada e aprovada por você antes de qualquer `INSERT`, no
   mesmo espírito da regra de ouro tributária do `AGENTS.md`.
5. **Migração**: nova migração Alembic aditiva (novas tabelas apenas), sem alterar tabelas
   existentes; chaves e constraints expressam os mesmos invariantes de imutabilidade já usados no
   catálogo (`0004_ibs_cbs_taxonomy`) e nas regras (`0001_governed_tax_rules`).
6. **Sem exposição pública ainda**: nenhum endpoint HTTP é criado nesta fase; o cadastro é
   alimentado apenas por seed/CLI de desenvolvimento e por uma futura carga governada análoga a
   `governed_load_cli.py`, que será objeto de ADR ou seção própria quando a fonte real for tratada.

## Consequências

- Desbloqueia, do ponto de vista de esquema, a futura implementação de `RT-IBSCBS-0007` e `0008` —
  mas não a autoriza sozinha: ainda faltam dados reais governados, testes e nova autorização
  específica para publicar qualquer `TaxRuleVersion`.
- Introduz mais uma tabela bitemporal a manter, com o mesmo custo operacional já aceito para regras
  e catálogo (ADR-0009).
- Risco principal: povoar a tabela com limites territoriais incorretos teria efeito prático
  equivalente a uma regra tributária errada. Mitigação: tratar a carga de dados reais como uma
  especificação sujeita a revisão e aprovação humana, nunca como carga técnica trivial.
- Não resolve, por si só, casos de fronteira geográfica fina (ex.: endereço ambíguo dentro de um
  município parcialmente abrangido); esses casos devem retornar `BOUNDARY`/`UNKNOWN` e
  `NECESSITA_VALIDACAO`, nunca uma inferência arbitrária.

## Alternativas consideradas

- **Codificar município/UF diretamente nas condições da regra**: rejeitado — já descartado pelo
  ADR-0021 por criar fonte paralela sem versão, vigência ou prova.
- **Adiar qualquer modelo até haver geometria completa**: rejeitado para a Fase 1 — a maioria dos
  fatos already exigidos pelas especificações 0007/0008 depende de habilitação/registro (Suframa),
  não de geometria fina; um cadastro por município/critério administrativo já destrava a maior
  parte dos casos, com geometria fina tratável em fase futura se a fonte oficial exigir.
- **Reaproveitar diretamente o modelo do catálogo cClassTrib para território**: rejeitado — são
  conceitos jurídicos distintos (classificação de operação vs. recorte territorial), com fontes e
  ciclos de vida próprios; acoplar os dois violaria a separação de agregados do ADR-0019.

## Critérios de revisão

Revisar antes de: (1) iniciar a migração e o código de domínio descritos aqui; (2) tratar geometria
fina ou importação automática de fonte oficial; (3) qualquer proposta de carregar dados reais de
território, que deve primeiro passar por pesquisa jurídica e aprovação específica, nos mesmos
moldes de uma especificação de regra tributária.
