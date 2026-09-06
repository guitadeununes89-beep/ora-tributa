"""Idempotent development-only identities. All names and identifiers are fictitious."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from argon2 import PasswordHasher
from sqlalchemy.orm import Session
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.identity_models import (
    CompanyRecord,
    MembershipRecord,
    OrganizationRecord,
    UserCredentialRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.session import get_engine


def seed() -> None:
    if get_settings().is_production:
        raise RuntimeError("Development identity seed is forbidden in production")
    password = os.environ.get("DEV_SEED_PASSWORD")
    if password is None or len(password) < 12:
        raise RuntimeError("Set DEV_SEED_PASSWORD with at least 12 characters")
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        if session.get(OrganizationRecord, "dev-org") is not None:
            return
        organization = OrganizationRecord(
            id="dev-org",
            name="Organização Fictícia de Desenvolvimento",
            slug="desenvolvimento",
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )
        user = UserRecord(
            id="dev-admin",
            email="admin@example.invalid",
            display_name="Administrador Fictício",
            status="ACTIVE",
            created_at=now,
            last_login_at=None,
        )
        session.add_all(
            [
                organization,
                user,
                UserCredentialRecord(
                    user_id=user.id,
                    password_hash=PasswordHasher().hash(password),
                    algorithm="argon2id",
                    updated_at=now,
                ),
                MembershipRecord(
                    id="dev-membership-admin",
                    organization_id=organization.id,
                    user_id=user.id,
                    role="ADMIN",
                    status="ACTIVE",
                    created_at=now,
                    updated_at=now,
                ),
                CompanyRecord(
                    id="dev-company",
                    organization_id=organization.id,
                    legal_name="Empresa Fictícia de Desenvolvimento Ltda.",
                    trade_name="Empresa Fictícia",
                    tax_id="00000000000000",
                    status="ACTIVE",
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()


if __name__ == "__main__":
    seed()
