# Acesso local de demonstração

## URLs

- frontend: `http://localhost:3000`;
- API: `http://localhost:8000`;
- OpenAPI: `http://localhost:8000/docs`;
- saúde: `http://localhost:8000/api/v1/health`.

## Usuários fictícios

- navegação e administração local: `demo@example.invalid`, papel `ADMIN`;
- execução da consulta piloto: `analyst@example.invalid`, papel `ANALYST`;
- organização: `governanca-tecnica-dev`;
- senha: valor definido localmente em `DEV_SEED_PASSWORD` ao executar o seed. A senha não é
  armazenada no Git.

`ADMIN` não é superusuário tributário: a segregação de funções impede que esse papel execute
avaliações. Use o ator `ANALYST` para o fluxo da RT-IBSCBS-0003. O seed de desenvolvimento é
idempotente e atualiza os hashes das credenciais fictícias para o valor corrente de
`DEV_SEED_PASSWORD`.

Para o ambiente local preparado nesta etapa foi usado `tributaria-demo-only`. Troque o valor se o
banco for compartilhado ou deixar de ser estritamente local.

## Iniciar após reiniciar o computador

PostgreSQL instalado como serviço:

```powershell
Start-Service postgresql-x64-17
```

API, no diretório raiz:

```powershell
$env:DEV_SEED_PASSWORD = "defina-uma-senha-local-com-12-ou-mais-caracteres"
.\.venv\Scripts\python.exe database/seeds/development_governance.py
.\.venv\Scripts\uvicorn.exe tributaria_api.main:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

Frontend, em outro terminal:

```powershell
$env:Path = "C:\caminho\para\node;" + $env:Path
pnpm --dir frontend dev
```

Se usar Docker em vez do serviço local, execute `docker compose up -d postgres`. Não suba duas
instâncias na porta 5432.
