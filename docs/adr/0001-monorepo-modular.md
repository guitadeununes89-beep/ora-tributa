# ADR-0001 — Monorepo modular e motor independente

- **Status:** Aceita
- **Data:** 2026-08-29

## Contexto

A plataforma terá interface web, API, importadores e um domínio fiscal complexo que precisa evoluir sem ficar acoplado a frameworks ou canais de entrada.

## Decisão

Adotar monorepo com `frontend`, `backend`, `tax-engine` e `importers` como unidades explícitas. O motor será biblioteca Python pura, sem FastAPI, ORM, banco ou rede. O backend será camada de aplicação/adaptação e dependerá do motor, nunca o inverso. Pacotes Python serão coordenados por workspace `uv`.

## Consequências

Testes do domínio serão rápidos e determinísticos; a API poderá mudar sem reescrever regras; importações terão ciclo próprio. O custo é disciplina adicional nas fronteiras e contratos entre pacotes.

## Alternativas consideradas

- Aplicação única Next.js: rejeitada porque misturaria o domínio Python e a interface.
- FastAPI monolítico com regras nos endpoints: rejeitado por acoplamento e baixa auditabilidade.
- Repositórios separados: adiado; aumentaria coordenação antes de haver equipes e ciclos independentes.

## Critérios de revisão

Reavaliar se equipes, permissões ou ciclos de release exigirem repositórios separados.

