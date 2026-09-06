# ADR-0004 — PostgreSQL e separação da persistência

- **Status:** Aceita
- **Data:** 2026-08-29

## Contexto

O produto precisa de integridade relacional, temporalidade, auditoria e consultas analíticas, mas o domínio não deve depender do mecanismo de persistência.

## Decisão

Adotar PostgreSQL como sistema transacional inicial. Repositórios serão portas da aplicação/domínio e implementações de persistência ficarão no backend. Migrações serão a única forma de alterar schema. Nenhuma tabela fiscal definitiva será criada antes de ADR do modelo temporal.

## Consequências

Há uma base madura para constraints e dados estruturados. Será necessário planejar particionamento/armazenamento analítico se volumes futuros justificarem; Polars poderá processar lotes fora do caminho transacional.

## Alternativas consideradas

- Banco documental primário: rejeitado pela menor força para invariantes relacionais/temporais.
- Data warehouse desde o início: rejeitado por complexidade prematura.

## Critérios de revisão

Reavaliar componentes analíticos após métricas reais de volume e latência.

