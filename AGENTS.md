# AGENTS.md — Regras de desenvolvimento

Este arquivo se aplica a todo o repositório. Arquivos `AGENTS.md` mais específicos podem adicionar restrições, mas não podem enfraquecer os princípios tributários, de segurança e auditoria abaixo.

## 1. Ordem de prioridade

1. correção jurídica e rastreabilidade;
2. preservação de dados e histórico;
3. segurança e privacidade;
4. correção técnica e testes;
5. clareza e manutenibilidade;
6. desempenho baseado em medição.

## 2. Regra de ouro tributária

- Nunca invente alíquota, classificação, exceção, benefício, crédito, vigência ou interpretação.
- Não transforme exemplo, hipótese, texto de interface ou resposta de IA em regra executável.
- Uma regra nova exige especificação aprovada com fundamento legal, fonte, dispositivo, jurisdição, início de vigência, eventual fim de vigência, versão e datas de inclusão/alteração.
- Fontes secundárias podem orientar pesquisa, mas a regra deve apontar para fonte normativa oficial ou registrar explicitamente a limitação.
- Em caso de ambiguidade ou falta de dados, interrompa a conclusão fiscal e produza estado de incerteza rastreável.

## 3. Imutabilidade e temporalidade

- Regra tributária publicada é imutável.
- Mudança legislativa ou correção cria nova versão; não faça `UPDATE` destrutivo do conteúdo histórico.
- Vigência jurídica e tempo de registro no sistema são conceitos diferentes e devem permanecer distinguíveis.
- Exclusão física de regra publicada é proibida. Use desativação/supersessão documentada quando aplicável.
- Reprocessamentos devem registrar a versão exata do motor, do conjunto de regras e dos dados de entrada.

## 4. Cálculo e classificação

- É proibido usar `float` para dinheiro, base, alíquota, quantidade fiscal ou resultado intermediário. Use `decimal.Decimal` no Python e representação decimal/string definida no contrato JSON.
- Arredondamento deve ser explícito, localizado e associado à norma aplicável. Não adote regra global implícita.
- NCM ou NBS isolados não autorizam conclusão quando a legislação exigir contexto adicional.
- Resultados de classificação permitidos: `CONCLUSIVO`, `POSSIVEIS_ENQUADRAMENTOS`, `NECESSITA_VALIDACAO`, `SEM_CLASSIFICACAO`.
- Nunca desempate arbitrariamente candidatos. Registre dados ausentes, hipóteses e caminhos descartados.
- Todo resultado deve fornecer uma trilha estruturada: entradas consideradas, regras avaliadas, condições satisfeitas/não satisfeitas, versões, fontes e etapas de cálculo.

## 5. Fronteiras arquiteturais

- `tax-engine` não pode importar FastAPI, SQLAlchemy, frameworks web, clientes HTTP nem componentes do frontend.
- O domínio define portas/contratos; adaptadores de banco, web e arquivos ficam fora do motor.
- `backend` orquestra casos de uso e converte contratos HTTP, sem concentrar lógica tributária.
- `frontend` não calcula tributos e não replica regra jurídica. Ele apresenta resultados e incertezas vindos da API.
- `importers` extrai e normaliza dados, preserva o original e relata erros; não decide enquadramento tributário.
- PostgreSQL é detalhe de persistência. Entidades do motor não devem depender de modelos ORM.
- Integrações externas devem ser encapsuladas e idempotentes quando possível.

## 6. Mudanças arquiteturais

- Antes de alterar fronteiras, banco, estratégia temporal, contratos públicos, autenticação, processamento assíncrono, infraestrutura ou política de cálculo, crie/atualize um ADR em `docs/adr/`.
- Um ADR deve conter contexto, decisão, consequências, alternativas e estado.
- Não esconda dívida técnica; registre-a com impacto e condição de resolução.

## 7. Testes obrigatórios

- Toda alteração no motor tributário exige testes automatizados.
- Toda regra futura exige exemplos positivos, negativos, limites de vigência, dados insuficientes e referência à especificação jurídica aprovada.
- Correção de bug exige teste de regressão.
- Testes não devem depender do relógio, rede ou ordem de execução sem controle explícito.
- Use testes unitários no domínio, integração para banco/adaptadores, contrato para API e ponta a ponta somente para jornadas críticas.
- Não reduza cobertura nem remova asserções para fazer a pipeline passar sem justificar a mudança.

## 8. Dados, segurança e observabilidade

- Nunca registre documentos fiscais completos, credenciais, tokens, certificados, chaves, CPFs/CNPJs ou dados pessoais sem mascaramento e necessidade explícita.
- Segredos pertencem ao ambiente/secret manager; `.env` nunca entra no Git.
- Todo upload futuro deve ter limite de tamanho, validação de tipo real, armazenamento seguro, quarentena e proteção contra XML malicioso.
- XML deve ser processado com rede e entidades externas desabilitadas.
- Logs estruturados devem usar `correlation_id`; trilha de auditoria de negócio não é substituída por log operacional.
- Autorizações devem ser verificadas no backend e preparadas para isolamento por organização (`tenant`).

## 9. Banco e migrações

- Toda mudança de schema ocorre por migração revisável; nunca dependa de alteração manual em ambiente.
- Migrações destrutivas exigem plano de preservação, rollback/roll-forward e aprovação explícita.
- Valores decimais usam `NUMERIC` com precisão/escala definidas; datas de vigência usam tipos temporais adequados e timezone quando representam instante.
- Chaves, constraints e índices devem expressar invariantes, não apenas otimizar consultas.

## 10. API e frontend

- APIs são versionadas (`/api/v1`) e usam modelos de entrada/saída explícitos.
- Erros públicos não expõem stack trace ou detalhes internos.
- Contratos monetários não usam JSON number quando houver risco de perda de precisão.
- Interfaces devem ser acessíveis, responsivas e deixar incerteza visível; não converter alerta em conclusão visual.
- Textos explicativos não devem ampliar o significado do resultado determinístico.

## 11. Fluxo de trabalho

Antes de editar:

1. leia a especificação, ADRs e instruções aplicáveis;
2. verifique o estado do Git e preserve alterações alheias;
3. identifique se a mudança toca lógica tributária ou decisão arquitetural;
4. se tocar regra fiscal, exija especificação jurídica antes de codificar.

Antes de concluir:

1. rode testes, lint e checagem de tipos proporcionais à mudança;
2. revise ausência de `float`, segredos, PII e dependências indevidas;
3. atualize documentação e ADRs;
4. descreva o que foi validado e qualquer limitação real.

## 12. Convenções

- Python 3.12+, typing estrito, Ruff e mypy; código e identificadores técnicos em inglês.
- TypeScript em modo `strict`; componentes acessíveis e preferencialmente server components quando não houver interatividade.
- Documentação de produto pode ser em português; termos legais devem manter a grafia oficial.
- Commits pequenos e descritivos; branches com prefixo `codex/` para trabalho automatizado.
- Dependências novas exigem justificativa, licença compatível e avaliação de manutenção/segurança.

## 13. Proibições explícitas nesta fase

- Não cadastrar regras, alíquotas, CST, cClassTrib, exceções ou benefícios reais.
- Não inferir tabelas oficiais a partir de memória do modelo.
- Não implementar autenticação, multi-tenancy ou ingestão fiscal completa sem ADR e especificação próprios.
- Não tratar os tipos-base existentes como modelo jurídico final; eles são contratos de segurança para evolução.

