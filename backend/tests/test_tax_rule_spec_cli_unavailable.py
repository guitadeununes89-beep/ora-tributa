from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.exc import OperationalError
from tributaria_api import tax_rule_spec_cli


def test_cli_returns_not_ready_when_reference_database_is_unavailable(
    monkeypatch,
    capsys,
) -> None:
    def unavailable_factory():
        raise OperationalError("statement", {}, RuntimeError("database unavailable"))

    monkeypatch.setattr(tax_rule_spec_cli, "get_session_factory", unavailable_factory)
    path = Path("docs/tax/rules/specifications/RT-IBSCBS-0001.json")

    exit_code = tax_rule_spec_cli.main([str(path), "--organization-id", "dev-org"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["readiness"] == "NOT_READY"
    assert output["issues"] == [
        {
            "code": "REFERENCE_LOOKUP_UNAVAILABLE",
            "path": "database",
            "message": (
                "Governed references could not be checked; no implementation is authorized"
            ),
        }
    ]
    assert "database unavailable" not in json.dumps(output)
