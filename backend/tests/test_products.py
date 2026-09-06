from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from tributaria_api.application.errors import NotFoundError
from tributaria_api.infrastructure.database import identity_models as _identity_models
from tributaria_api.infrastructure.database import product_models as _product_models
from tributaria_api.infrastructure.database import taxonomy_models as _taxonomy_models
from tributaria_api.infrastructure.database.identity_models import OrganizationRecord, UserRecord
from tributaria_api.infrastructure.database.models import Base
from tributaria_api.infrastructure.database.product_repository import ProductRepository

assert _identity_models and _product_models and _taxonomy_models


def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def functions(connection: object, _: object) -> None:
        connection.create_function("char_length", 1, len)  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    result = Session(engine)
    now = datetime(2040, 1, 1, tzinfo=UTC)
    result.add_all(
        [
            OrganizationRecord(
                id="org-a", name="A", slug="a", status="ACTIVE", created_at=now, updated_at=now
            ),
            OrganizationRecord(
                id="org-b", name="B", slug="b", status="ACTIVE", created_at=now, updated_at=now
            ),
            UserRecord(
                id="user",
                email="user@example.invalid",
                display_name="User",
                status="ACTIVE",
                created_at=now,
                last_login_at=None,
            ),
        ]
    )
    result.commit()
    return result


def product_data() -> dict[str, object]:
    return {
        "internal_code": "SKU-1",
        "description": "Synthetic product fixture",
        "gtin": None,
        "ncm": None,
        "cest": None,
        "unit": "UN",
        "status": "ACTIVE",
        "attributes": [{"key": "synthetic.required", "value": "YES", "is_synthetic": True}],
        "change_reason": "Synthetic creation",
    }


def test_product_create_update_and_history_are_immutable_snapshots() -> None:
    db = session()
    repository = ProductRepository(db)
    first = repository.create("org-a", "user", datetime(2040, 1, 2, tzinfo=UTC), product_data())
    db.commit()

    second = repository.update(
        "org-a",
        str(first["id"]),
        "user",
        datetime(2040, 1, 3, tzinfo=UTC),
        {"ncm": "12345678", "change_reason": "Synthetic NCM history test"},
    )
    db.commit()

    assert second["current_version"] == 2
    assert second["current"]["ncm"] == "12345678"
    assert second["history"][1]["ncm"] is None
    assert second["history"][0]["snapshot_hash"] != second["history"][1]["snapshot_hash"]
    assert second["history"][0]["attributes"] == second["history"][1]["attributes"]


def test_product_is_not_visible_cross_tenant() -> None:
    db = session()
    repository = ProductRepository(db)
    product = repository.create("org-a", "user", datetime(2040, 1, 2, tzinfo=UTC), product_data())
    db.commit()

    with pytest.raises(NotFoundError):
        repository.get("org-b", str(product["id"]))
    assert repository.list_products("org-b") == []
