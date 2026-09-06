from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from tributaria_api.application.tax_rule_specifications import (
    TaxRuleSpecificationValidator,
    load_specification,
)
from tributaria_api.infrastructure.database.session import get_session_factory
from tributaria_api.infrastructure.database.tax_rule_spec_lookup import (
    SqlAlchemySpecificationReferenceLookup,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate-tax-rule-spec",
        description=(
            "Validate structural readiness and governed references without judging legal merit."
        ),
    )
    parser.add_argument("file", type=Path, help="JSON specification file")
    parser.add_argument("--organization-id", required=True)
    return parser


def _disclaimer() -> str:
    return "Structural readiness does not attest to the correctness of legal interpretation."


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = load_specification(args.file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "readiness": "NOT_READY",
                    "issues": [
                        {
                            "code": "DOCUMENT_INVALID",
                            "path": str(args.file),
                            "message": str(exc),
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    try:
        with get_session_factory()() as session:
            validator = TaxRuleSpecificationValidator(
                SqlAlchemySpecificationReferenceLookup(session)
            )
            result = validator.validate(document, args.organization_id)
    except SQLAlchemyError:
        print(
            json.dumps(
                {
                    "readiness": "NOT_READY",
                    "rule_id": document.get("rule_id"),
                    "specification_version": document.get("specification_version"),
                    "issues": [
                        {
                            "code": "REFERENCE_LOOKUP_UNAVAILABLE",
                            "path": "database",
                            "message": (
                                "Governed references could not be checked; "
                                "no implementation is authorized"
                            ),
                        }
                    ],
                    "disclaimer": _disclaimer(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "readiness": result.readiness,
                "rule_id": result.specification.rule_id if result.specification else None,
                "specification_version": (
                    result.specification.specification_version if result.specification else None
                ),
                "issues": [
                    {"code": issue.code, "path": issue.path, "message": issue.message}
                    for issue in result.issues
                ],
                "disclaimer": _disclaimer(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.readiness == "READY_FOR_IMPLEMENTATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
