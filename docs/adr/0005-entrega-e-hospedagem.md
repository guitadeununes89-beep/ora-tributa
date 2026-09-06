# ADR-0005 — Entrega local e hospedagem agnóstica

- **Status:** Aceita
- **Data:** 2026-08-29

## Contexto

Esta etapa pede fundação do repositório, não implantação. Starters de hospedagem opinativos podem conflitar com Next.js + FastAPI + PostgreSQL e criar acoplamento prematuro.

## Decisão

Preparar execução local e CI portável, sem escolher provedor de nuvem nem publicar ambiente. Contêineres de aplicação e infraestrutura de produção serão definidos depois de requisitos de segurança, residência de dados, disponibilidade e custo.

## Consequências

O produto não fica preso a um provedor e mantém o escopo da fundação. Não haverá URL pública nesta etapa.

## Alternativas consideradas

- Publicar imediatamente em plataforma de sites: rejeitada por antecipar decisões de segurança, backend e banco.
- Definir Kubernetes agora: rejeitada por complexidade sem necessidade validada.

## Critérios de revisão

Criar novo ADR antes do primeiro ambiente compartilhado.

