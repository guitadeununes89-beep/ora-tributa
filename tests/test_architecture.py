from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_TAX_ENGINE_IMPORTS = {
    "django",
    "fastapi",
    "flask",
    "frontend",
    "next",
    "react",
    "sqlalchemy",
}


def test_tax_engine_does_not_import_frameworks() -> None:
    source_root = Path(__file__).parents[1] / "tax-engine" / "src"
    violations: list[str] = []

    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".", maxsplit=1)[0] in FORBIDDEN_TAX_ENGINE_IMPORTS:
                    violations.append(f"{path}: {name}")

    assert violations == []
