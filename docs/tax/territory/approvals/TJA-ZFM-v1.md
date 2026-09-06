# Evidência de revisão e aprovação — TJA-ZFM v1

- **Especificação:** TJA-ZFM
- **Versão:** 1
- **Data da declaração:** 2026-09-06
- **Revisor e aprovador:** Guilherme Nunes
- **Capacidade declarada:** responsável tributário e jurídico do projeto
- **Ator governado:** `legal-approver-guilherme-nunes`
- **Escopo:** definição territorial da Zona Franca de Manaus para fins de IBS/CBS, conforme
  Decreto-Lei nº 288/1967 (arts. 1º e 2º), Decreto nº 61.244/1967 (art. 2º), LC nº 214/2025 (art.
  439) e Resolução CGIBS nº 6/2026 (art. 433, I), abrangendo parte dos Municípios de Manaus, Rio
  Preto da Eva e Itacoatiara.

## Declaração registrada

O responsável declarou aprovação da especificação v1 de `TJA-ZFM`, **com ciência expressa dos
quatro itens listados em `known_conflicts`** (proposta de ampliação às 12/13 cidades da Grande
Manaus ainda não vigente; Decreto-Lei nº 288/1967 não lido em texto consolidado integral; decisão
pendente sobre fixar `effective_to` em 2073 conforme art. 92-A do ADCT; habilitação/registro
Suframa como fato separado, fora do escopo deste documento). Nenhum desses itens foi resolvido por
esta aprovação — permanecem registrados como limitações conhecidas.

Esta aprovação autoriza o avanço do status documental de `DRAFT` para `APPROVED`. **Não autoriza,
por si só**, carregar `TaxJurisdictionAreaVersion` real, criar migração de dados, nem alterar o
comportamento do resolvedor (`application/territory.py`). A carga de dado real exige, no mínimo, a
criação de um CLI/seed governado próprio (ainda não construído) e nova autorização específica para
essa etapa.

Esta evidência não contém CPF, documento pessoal, credencial ou segredo.
