# Etapa 9.3 — aprovação jurídica humana de RT-IBSCBS-0007 e RT-IBSCBS-0008

- **Data:** 2026-09-06
- **Ator:** Guilherme Nunes, na capacidade de responsável tributário e jurídico do projeto
  (`legal-approver-guilherme-nunes`), a mesma capacidade já exercida na aprovação de
  `RT-IBSCBS-0003` (`docs/tax/rules/approvals/RT-IBSCBS-0003-v2.md`).

## O que mudou

Após revisar a delimitação registrada em `docs/tax/ETAPA_9_1_FINAL_APPROVAL_MATRIX.md` — sem
nenhuma alteração de conteúdo jurídico —, o responsável aprovou integralmente:

- `RT-IBSCBS-0007` v3 (cClassTrib `200022`, art. 445 da LC nº 214/2025);
- `RT-IBSCBS-0008` v3 (cClassTrib `200023`, art. 448 da LC nº 214/2025).

Cada especificação teve seu campo `status` alterado de `DRAFT` para `APPROVED` e seu bloco
`approval` preenchido (`reviewed_by`, `approved_by`, `approval_date`, `approval_evidence`), com
evidência registrada em:

- `docs/tax/rules/approvals/RT-IBSCBS-0007-v3.md`;
- `docs/tax/rules/approvals/RT-IBSCBS-0008-v3.md`.

`RT-IBSCBS-0009` **não foi aprovada** e permanece `DRAFT`/`BLOCKED_LEGAL_REFERENCE_CONFLICT`: a
divergência entre o art. 456 citado pelo catálogo oficial e o art. 460 exigido pela cadeia legal
(LC nº 214/2025, LC nº 227/2026 e Resolução CGIBS nº 6/2026) continua sem retificação oficial
localizada, e nenhuma aprovação é permitida enquanto ela persistir.

## O que NÃO mudou

- **A cobertura executável permanece `1/164` (`0,61%`).** Aprovação jurídica isolada não cria
  `TaxRuleVersion`, não publica ruleset e não altera o comportamento do `tax-engine`, exatamente
  como registrado em `ETAPA_9_1_FINAL_APPROVAL_MATRIX.md`.
- Nenhum código, alíquota, exceção ou interpretação foi criado, alterado ou inferido nesta etapa;
  apenas o estado documental de aprovação das duas especificações já delimitadas.
- A implementação executável de `RT-IBSCBS-0007` e `RT-IBSCBS-0008` continua exigindo, no mínimo:
  1. nova autorização específica para avaliar a implementação (separada desta aprovação);
  2. a carga governada do território da Zona Franca de Manaus (`TaxJurisdictionArea`, decidido no
     ADR-0021, ainda sem tabela, migração ou dado real — bloqueador `NEEDS_GOVERNED_ZFM_TERRITORY_
     AND_OPERATIONAL_ACTS` registrado em ambas as especificações);
  3. testes automatizados e pré-flight real `READY_FOR_IMPLEMENTATION` contra o banco governado.

## Rastreabilidade

Os hashes SHA-256 abaixo foram calculados sobre o conteúdo normalizado (LF) dos arquivos de
evidência, e são os mesmos valores referenciados em `approval.approval_evidence` de cada
especificação:

- `RT-IBSCBS-0007-v3.md`: `0f39fbd410e5c90d24deb8cb9105bf59001af1c05c4d218e6d9b5007a77e1caa`
- `RT-IBSCBS-0008-v3.md`: `aff541c9a35f4f67b68809d4bb02ff599234e2b57c27163d6962ea2842731ad1`
