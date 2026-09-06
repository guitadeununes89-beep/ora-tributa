from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from tributaria_api.application.security import AuthContext, Permission, Role
from tributaria_api.infrastructure.database.identity_models import (
    CompanyRecord,
    MembershipRecord,
    OrganizationRecord,
    UserCredentialRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.models import AuditEventRecord, Base
from tributaria_api.infrastructure.database.session import get_session
from tributaria_api.main import create_app

NOW = datetime(2040, 1, 1, tzinfo=UTC)


@pytest.fixture
def api() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def sqlite_functions(connection: object, _: object) -> None:
        connection.create_function("char_length", 1, len)  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    org_a = OrganizationRecord(
        id="org-a",
        name="Organização Fictícia A",
        slug="org-a",
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
    org_b = OrganizationRecord(
        id="org-b",
        name="Organização Fictícia B",
        slug="org-b",
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
    user = UserRecord(
        id="user-admin",
        email="admin@example.invalid",
        display_name="Admin Fictício",
        status="ACTIVE",
        created_at=NOW,
        last_login_at=None,
    )
    analyst = UserRecord(
        id="user-analyst",
        email="analyst@example.invalid",
        display_name="Analista Fictício",
        status="ACTIVE",
        created_at=NOW,
        last_login_at=None,
    )
    session.add_all([org_a, org_b, user, analyst])
    hasher = PasswordHasher()
    session.add_all(
        [
            UserCredentialRecord(
                user_id=user.id,
                password_hash=hasher.hash("safe-test-password"),
                algorithm="argon2id",
                updated_at=NOW,
            ),
            UserCredentialRecord(
                user_id=analyst.id,
                password_hash=hasher.hash("safe-test-password"),
                algorithm="argon2id",
                updated_at=NOW,
            ),
            MembershipRecord(
                id="membership-admin",
                organization_id=org_a.id,
                user_id=user.id,
                role="ADMIN",
                status="ACTIVE",
                created_at=NOW,
                updated_at=NOW,
            ),
            MembershipRecord(
                id="membership-analyst",
                organization_id=org_a.id,
                user_id=analyst.id,
                role="ANALYST",
                status="ACTIVE",
                created_at=NOW,
                updated_at=NOW,
            ),
            CompanyRecord(
                id="company-other-tenant",
                organization_id=org_b.id,
                legal_name="Empresa Fictícia B",
                trade_name=None,
                tax_id="99999999999999",
                status="ACTIVE",
                created_at=NOW,
                updated_at=NOW,
            ),
        ]
    )
    session.commit()

    def session_override():  # type: ignore[no-untyped-def]
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = session_override
    with TestClient(app) as client:
        yield client, session
    session.close()


def login(client: TestClient, email: str = "admin@example.invalid") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "safe-test-password",
            "organization_slug": "org-a",
        },
    )
    assert response.status_code == 200
    return client.cookies["tributaria_csrf"]


def test_valid_and_invalid_login_do_not_expose_credential_details(api) -> None:  # type: ignore[no-untyped-def]
    client, session = api
    invalid = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.invalid",
            "password": "wrong",
            "organization_slug": "org-a",
        },
    )
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.invalid", "password": "wrong", "organization_slug": "org-a"},
    )
    assert invalid.status_code == wrong_password.status_code == 401
    assert invalid.json() == wrong_password.json()
    login(client)
    assert client.get("/api/v1/auth/me").json()["role"] == "ADMIN"
    assert (
        session.scalar(select(AuditEventRecord).where(AuditEventRecord.action == "LOGIN_SUCCEEDED"))
        is not None
    )


def test_unauthenticated_and_insufficient_role_are_rejected(api) -> None:  # type: ignore[no-untyped-def]
    client, _ = api
    assert client.get("/api/v1/companies").status_code == 401
    csrf = login(client, "analyst@example.invalid")
    response = client.post(
        "/api/v1/companies",
        headers={"X-CSRF-Token": csrf},
        json={"legal_name": "Empresa Teste", "trade_name": None, "tax_id": "11111111111111"},
    )
    assert response.status_code == 403


def test_company_establishment_tenant_and_audit(api) -> None:  # type: ignore[no-untyped-def]
    client, session = api
    csrf = login(client)
    response = client.post(
        "/api/v1/companies",
        headers={"X-CSRF-Token": csrf, "X-Correlation-ID": "corr-company"},
        json={
            "legal_name": "Empresa Fictícia A",
            "trade_name": "Teste",
            "tax_id": "11111111111111",
        },
    )
    assert response.status_code == 201
    company_id = response.json()["id"]
    assert {item["id"] for item in client.get("/api/v1/companies").json()} == {company_id}
    assert "company-other-tenant" not in client.get("/api/v1/companies").text
    establishment = client.post(
        f"/api/v1/companies/{company_id}/establishments",
        headers={"X-CSRF-Token": csrf},
        json={
            "tax_id": "22222222222222",
            "name": "Filial Fictícia",
            "state": "SP",
            "municipality": "Município Fictício",
        },
    )
    assert establishment.status_code == 201
    actions = set(session.scalars(select(AuditEventRecord.action)))
    assert {"COMPANY_CREATED", "ESTABLISHMENT_CREATED"} <= actions


def test_membership_update_is_tenant_scoped_and_audited(api) -> None:  # type: ignore[no-untyped-def]
    client, session = api
    csrf = login(client)
    response = client.patch(
        "/api/v1/memberships/membership-analyst",
        headers={"X-CSRF-Token": csrf},
        json={"role": "VIEWER"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "VIEWER"
    assert (
        session.scalar(
            select(AuditEventRecord).where(AuditEventRecord.action == "MEMBERSHIP_CHANGED")
        )
        is not None
    )
    missing = client.patch(
        f"/api/v1/memberships/{uuid4()}",
        headers={"X-CSRF-Token": csrf},
        json={"role": "VIEWER"},
    )
    assert missing.status_code == 404


def test_rbac_is_explicit_and_non_hierarchical() -> None:
    context = AuthContext(
        session_id="s",
        user_id="u",
        email="u@example.invalid",
        display_name="U",
        organization_id="o",
        organization_name="O",
        membership_id="m",
        role=Role.ADMIN,
    )
    assert Permission.MANAGE_MEMBERSHIP in context.permissions
    assert Permission.APPROVE_RULE not in context.permissions
