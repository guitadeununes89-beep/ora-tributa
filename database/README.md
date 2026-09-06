# PostgreSQL e migrações

O schema governado é definido exclusivamente por Alembic em `database/migrations`. Alterações manuais em ambientes compartilhados são proibidas.

```bash
docker compose up -d postgres
uv sync --all-packages --dev
uv run alembic upgrade head
```

- `0001_governed_tax_rules`: tabelas, chaves, checks, índices e proteção append-only inicial;
- `0002_harden_governance_constraints`: continuidade do lifecycle e membros publicados do ruleset;
- `seeds/development_synthetic.py`: dados fictícios `TEST-*`, restritos a desenvolvimento.

O modelo e suas invariantes estão em `docs/PERSISTENCE_MODEL.md` e nos ADRs 0009–0011. Migrações destrutivas futuras exigem plano explícito de preservação e roll-forward/rollback.