# Roadmap de cobertura — Imposto Seletivo

## Estado atual

O Imposto Seletivo é domínio autônomo. Nesta etapa não existe regra de IS publicada, cálculo real,
alíquota cadastrada nem cobertura executável. Classificar um bem, serviço ou operação como candidato
não é calcular o imposto.

Base oficial consolidada:

- Constituição, art. 153, VIII e § 6º, incluído pela
  [EC 132/2023](https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm);
- [LC 214/2025 compilada](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm),
  arts. 409 a 438 e Anexo XVII;
- [LC 227/2026](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm), que alterou pontos de
  base, sujeitos, minerais, transições setoriais e importação.

## Duas trilhas obrigatórias

### A. Classificação e incidência

1. identificar o tipo de objeto tributável e a operação;
2. confrontar categorias do Anexo XVII e demais condições legais;
3. avaliar não incidência, exportação, energia/telecom e hipóteses específicas;
4. emitir conclusão, possíveis enquadramentos, necessidade de validação ou ausência de classificação;
5. produzir `DecisionTrace` com fonte e versão.

### B. Cálculo

1. determinar fato gerador e sujeito passivo;
2. determinar espécie de base aplicável — valor, referência, unidade de medida ou outra prevista;
3. resolver interações de base;
4. localizar alíquota ad valorem ou específica em lei ordinária vigente;
5. aplicar regras de devolução, exportação, importação e responsabilidade quando cabíveis;
6. produzir `TaxComputationResult` e `CalculationTrace`.

Uma trilha A conclusiva não torna a trilha B calculável.

## Mapa jurídico mínimo

| Tema | Conteúdo a especificar | Referência oficial | Estado |
|---|---|---|---|
| Incidência | produção, extração, comercialização ou importação dos bens e serviços legalmente abrangidos | LC 214/2025, art. 409 e Anexo XVII | Identificado; não executável |
| Incidência única | uma única incidência e ausência de aproveitamento de créditos de operações anteriores ou geração para posteriores | LC 214/2025, art. 410 | Identificado; não executável |
| Momento do fato gerador | hipóteses distintas de fornecimento, arrematação, transferência, incorporação, extração, consumo, serviço e importação | LC 214/2025, art. 412 | Exige fatos por hipótese |
| Não incidência | energia elétrica, telecomunicações e demais hipóteses constitucionais/legais, incluindo o tratamento próprio das exportações | Constituição, art. 153, § 6º; LC 214/2025, art. 413 | Exige revisão por família e exceção mineral |
| Base | valor da operação, arrematação, valor de referência, valor contábil, receita ou valor de mercado, conforme hipótese | LC 214/2025, arts. 414 a 417, com alterações da LC 227/2026 | Identificado; depende de hipótese |
| Alíquota | ad valorem e/ou específica conforme família, a ser estabelecida por lei ordinária | LC 214/2025, arts. 419 a 423 e 436 | Bloqueada sem fonte de alíquota vigente |
| Devolução | abatimento disciplinado para bem devolvido | LC 214/2025, art. 418 | Não equivale a crédito genérico |
| Importação | base, sujeito e tratamentos próprios | LC 214/2025, arts. 434 a 436, com alterações da LC 227/2026 | Identificado; não executável |
| Exportação | não incidência e disciplina da saída com fim específico de exportação/responsabilidade | Constituição, art. 153, § 6º; LC 214/2025, arts. 426 e 427 | Exige prova e tratamento da extração mineral |
| Vigência | cobrança constitucionalmente prevista a partir de 2027 | ADCT, art. 126 | Período documentado; sem cálculo |

## Fatos necessários a governar

O conjunto varia por família e poderá incluir, apenas com fundamento específico: data e tipo da
operação; natureza do objeto; classificação oficial; fabricante/importador/extrator/prestador;
primeiro fornecimento; país de origem e destino; exportação e prova; valor da operação, valor de
referência, unidade de medida e quantidade; composição, teor, potência, eficiência, uso/destinação;
devolução; partes relacionadas; consumo ou incorporação pelo fabricante; e dados aduaneiros.

## Tabelas e atos ainda necessários

- Anexo XVII vigente e suas versões;
- NCM/TIPI e outros classificadores oficiais efetivamente citados pela norma;
- lei ordinária vigente de alíquotas ad valorem/específicas;
- valores de referência, unidades de medida e atos regulamentares oficiais quando exigidos;
- versões de regras aduaneiras e setoriais aplicáveis.

Nenhuma dessas fontes será reconstruída por memória ou descrição de interface.

## Famílias iniciais e dependências

| Família legal | Referência | Dependência principal | Prioridade sugerida |
|---|---|---|---|
| Veículos | Anexo XVII; arts. 409 e 419 | identificação técnica, exceções e lei de alíquotas | P1 após fonte de alíquota |
| Embarcações e aeronaves | Anexo XVII; arts. 409 e 420 | classificação objetiva e lei de alíquotas | P2 |
| Produtos fumígenos | Anexo XVII; arts. 409, 421 e 434 | alíquota ad valorem/específica e regras de importação | P1 após fonte de alíquota |
| Bebidas alcoólicas | Anexo XVII; arts. 409 e 421 | alíquota, teor e unidade aplicável | P1 após fonte de alíquota |
| Bebidas açucaradas | Anexo XVII; arts. 409 e 421 | composição/classificação e alíquota | P2 |
| Bens minerais | Anexo XVII; arts. 409 e 422 | extração, base, destino e alíquota dentro do limite legal | P1 após fonte de alíquota |
| Concursos de prognósticos e fantasy sport | Anexo XVII; arts. 409 e 423 | receita-base, evento e alíquota | P2 |

## Bloqueadores

- A LC 214 determina que as alíquotas serão estabelecidas por lei ordinária. Nenhuma alíquota deve
  ser inferida dos limites, transições ou exemplos.
- Tabelas/classificações técnicas e regulamentação infralegal aplicáveis devem ser governadas e
  versionadas antes da execução.
- Fatos para composição, uso, potência, eficiência, teor, unidade, extração e destinação variam por
  família e não podem ser generalizados.

## Critério de avanço

Cada família percorre `SOURCE CHECK → SPEC → LEGAL REVIEW → HUMAN APPROVAL → IMPLEMENTATION →`
`PUBLICATION`. Até esse ciclo ser completado, a cobertura executável de IS é zero e a resposta de
cálculo deve ser `REQUIRES_VALIDATION`.
