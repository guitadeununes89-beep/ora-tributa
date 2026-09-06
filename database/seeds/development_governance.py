"""Idempotent, fictitious identities for governed development workflows."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from argon2 import PasswordHasher
from sqlalchemy.orm import Session
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.identity_models import (
    MembershipRecord,
    OrganizationRecord,
    UserCredentialRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.session import get_engine

ORGANIZATION_ID = "dev-governance-org"
ACTORS = (
    ("dev-demo", "demo@example.invalid", "Demonstração Fictícia", "ADMIN"),
    ("dev-analyst", "analyst@example.invalid", "Analista Fictício", "ANALYST"),
    ("dev-curator", "curator@example.invalid", "Curador Fictício", "CURATOR"),
    ("dev-approver", "approver@example.invalid", "Aprovador Fictício", "APPROVER"),
    ("dev-publisher", "publisher@example.invalid", "Publicador Fictício", "PUBLISHER"),
)


def seed() -> None:
    if get_settings().is_production:
        raise RuntimeError("Development governance seed is forbidden in production")
    password = os.environ.get("DEV_SEED_PASSWORD")
    if password is None or len(password) < 12:
        raise RuntimeError("Set DEV_SEED_PASSWORD with at least 12 characters")
    now = datetime.now(UTC)
    hasher = PasswordHasher()
    with Session(get_engine()) as session:
        organization = session.get(OrganizationRecord, ORGANIZATION_ID)
        if organization is None:
            session.add(
                OrganizationRecord(
                    id=ORGANIZATION_ID,
                    name="Organização Técnica Fictícia de Governança",
                    slug="governanca-tecnica-dev",
                    status="ACTIVE",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
        for user_id, email, display_name, role in ACTORS:
            if session.get(UserRecord, user_id) is None:
                session.add(
                    UserRecord(
                        id=user_id,
                        email=email,
                        display_name=display_name,
                        status="ACTIVE",
                        created_at=now,
                        last_login_at=None,
                    )
                )
                session.flush()
            credential = session.get(UserCredentialRecord, user_id)
            if credential is None:
                session.add(
                    UserCredentialRecord(
                        user_id=user_id,
                        password_hash=hasher.hash(password),
                        algorithm="argon2id",
                        updated_at=now,
                    )
                )
            else:
                credential.password_hash = hasher.hash(password)
                credential.algorithm = "argon2id"
                credential.updated_at = now
            membership_id = f"membership-{user_id}"
            if session.get(MembershipRecord, membership_id) is None:
                session.add(
                    MembershipRecord(
                        id=membership_id,
                        organization_id=ORGANIZATION_ID,
                        user_id=user_id,
                        role=role,
                        status="ACTIVE",
                        created_at=now,
                        updated_at=now,
                    )
                )
        session.commit()


if __name__ == "__main__":
    seed()

