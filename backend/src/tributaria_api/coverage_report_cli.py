from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from tributaria_api.application.coverage import (
    build_national_coverage,
    load_specification_documents,
)
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.repositories import (
    SqlAlchemyGovernanceRepository,
)
from tributaria_api.infrastructure.database.session import get_engine
from tributaria_api.infrastructure.database.taxonomy_repository import (
    SqlAlchemyTaxonomyRepository,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the governed IBS/CBS coverage matrix")
    parser.add_argument("--organization-id", default="dev-governance-org")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/tax/IBSCBS_NATIONAL_COVERAGE_MATRIX.md"),
    )
    args = parser.parse_args()
    settings = get_settings()
    with Session(get_engine()) as session:
        taxonomy = SqlAlchemyTaxonomyRepository(session)
        governance = SqlAlchemyGovernanceRepository(session)
        projection = build_national_coverage(
            taxonomy.list_classifications(args.organization_id),
            load_specification_documents(Path(settings.tax_rule_specification_root).resolve()),
            [
                value
                for value in governance.list_rule_versions()
                if value.get("organization_id") == args.organization_id
            ],
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_markdown(projection), encoding="utf-8")
    return 0


def _markdown(projection: dict[str, Any]) -> str:
    metrics = projection["metrics"]
    catalog = projection["catalog"]
    lines = [
        "# Matriz nacional de cobertura IBS/CBS",
        "",
        "> Inventário derivado do snapshot oficial `PUBLISHED`. cClassTrib não é TaxRule e o",
        "> conteúdo desta matriz não autoriza execução tributária.",
        "",
        "## Snapshot e métricas",
        "",
        f"- versão: `{catalog['version']}` (`{catalog['version_id']}`);",
        f"- documento: {catalog['technical_document']};",
        f"- SHA-256: `{catalog['artifact_hash']}`;",
        f"- total: **{metrics['total_cclasstrib']}** cClassTrib;",
        f"- fundamento oficial estruturado: **{metrics['foundation_identified']}**;",
        f"- especificação DRAFT: **{metrics['draft_specification']}**;",
        f"- publicados/executáveis: **{metrics['published']}**;",
        f"- cobertura executável: **{metrics['published']}/{metrics['total_cclasstrib']} "
        f"({metrics['executable_percentage']}%)**.",
        "",
        "## Inventário completo",
        "",
        "| CST | cClassTrib | Descrição oficial | Fundamento/dispositivo | Vigência | "
        "Indicadores oficiais não vazios | Catálogo | Cobertura | Especificações | Regras |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in projection["items"]:
        indicators = ", ".join(
            f"{key}={value}"
            for key, value in item["indicators"].items()
            if value not in (None, "", 0, False)
            and key not in {"LCRedação", "RegulamentoCBS", "RegulamentoIBS", "Link"}
        )
        validity = f"{item['valid_from'] or 'não informada'} → {item['valid_to'] or 'aberta'}"
        specifications = (
            ", ".join(f"{value['rule_id']} ({value['status']})" for value in item["specifications"])
            or "—"
        )
        rules = (
            ", ".join(
                f"{value['rule_code']} v{value['version']} ({value['status']})"
                for value in item["rules"]
            )
            or "—"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(item["cst"]),
                    _cell(item["cclasstrib"]),
                    _cell(item["official_description"]),
                    _cell(item["legal_device"] or "Não estruturado no snapshot"),
                    _cell(validity),
                    _cell(indicators or "—"),
                    _cell(item["catalog_version"]),
                    _cell(item["coverage_status"]),
                    _cell(specifications),
                    _cell(rules),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Leitura correta",
            "",
            "- `LEGAL_MAPPING_REQUIRED` indica fundamento oficial no catálogo sem especificação;",
            "- `CATALOG_ONLY` indica ausência de dispositivo estruturado no snapshot;",
            "- `PUBLISHED` indica ao menos uma regra publicada, não cobertura integral do código;",
            "- descrições e indicadores oficiais não foram convertidos em condições executáveis.",
            "",
        ]
    )
    return "\n".join(lines)


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
