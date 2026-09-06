from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.infrastructure.database.identity_models import (
    AuthSessionRecord,
    CompanyRecord,
    EstablishmentRecord,
    MembershipRecord,
    OrganizationRecord,
    UserCredentialRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.models import AuditEventRecord


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def login_candidate(self, email: str, organization_slug: str) -> Any:
        statement = (
            select(UserRecord, UserCredentialRecord, OrganizationRecord, MembershipRecord)
            .join(UserCredentialRecord, UserCredentialRecord.user_id == UserRecord.id)
            .join(MembershipRecord, MembershipRecord.user_id == UserRecord.id)
            .join(OrganizationRecord, OrganizationRecord.id == MembershipRecord.organization_id)
            .where(
                UserRecord.email == email.casefold().strip(),
                OrganizationRecord.slug == organization_slug.casefold().strip(),
                UserRecord.status == "ACTIVE",
                OrganizationRecord.status == "ACTIVE",
                MembershipRecord.status == "ACTIVE",
            )
        )
        return self.session.execute(statement).one_or_none()

    def create_session(self, **data: object) -> AuthSessionRecord:
        record = AuthSessionRecord(**data)
        self.session.add(record)
        self.session.commit()
        return record

    def resolve_session(self, token_hash: str, now: datetime) -> Any:
        statement = (
            select(
                AuthSessionRecord,
                UserRecord,
                OrganizationRecord,
                MembershipRecord,
            )
            .join(UserRecord, UserRecord.id == AuthSessionRecord.user_id)
            .join(OrganizationRecord, OrganizationRecord.id == AuthSessionRecord.organization_id)
            .join(MembershipRecord, MembershipRecord.id == AuthSessionRecord.membership_id)
            .where(
                AuthSessionRecord.token_hash == token_hash,
                AuthSessionRecord.revoked_at.is_(None),
                AuthSessionRecord.expires_at > now,
                UserRecord.status == "ACTIVE",
                OrganizationRecord.status == "ACTIVE",
                MembershipRecord.status == "ACTIVE",
                MembershipRecord.user_id == AuthSessionRecord.user_id,
                MembershipRecord.organization_id == AuthSessionRecord.organization_id,
            )
        )
        return self.session.execute(statement).one_or_none()

    def revoke_session(self, token_hash: str, now: datetime) -> None:
        record = self.session.scalar(
            select(AuthSessionRecord).where(AuthSessionRecord.token_hash == token_hash)
        )
        if record is not None and record.revoked_at is None:
            record.revoked_at = now
            self.session.commit()

    def record_audit(
        self,
        *,
        organization_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        occurred_at: datetime,
        correlation_id: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.session.add(
            AuditEventRecord(
                id=str(uuid4()),
                organization_id=organization_id,
                authenticated_user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                occurred_at=occurred_at,
                actor_id=user_id,
                origin="authenticated-api",
                correlation_id=correlation_id,
                safe_metadata=metadata or {},
            )
        )

    def list_companies(self, organization_id: str) -> list[CompanyRecord]:
        return list(
            self.session.scalars(
                select(CompanyRecord)
                .where(CompanyRecord.organization_id == organization_id)
                .order_by(CompanyRecord.legal_name)
            )
        )

    def get_company(self, organization_id: str, company_id: str) -> CompanyRecord:
        record = self.session.scalar(
            select(CompanyRecord).where(
                CompanyRecord.id == company_id,
                CompanyRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise NotFoundError("Company not found")
        return record

    def create_company(self, organization_id: str, now: datetime, **data: object) -> CompanyRecord:
        record = CompanyRecord(
            id=str(uuid4()),
            organization_id=organization_id,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
            **data,
        )
        self.session.add(record)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Company already exists in this organization") from exc
        return record

    def set_company_status(
        self, organization_id: str, company_id: str, status: str, now: datetime
    ) -> CompanyRecord:
        record = self.get_company(organization_id, company_id)
        record.status = status
        record.updated_at = now
        self.session.flush()
        return record

    def list_establishments(
        self, organization_id: str, company_id: str
    ) -> list[EstablishmentRecord]:
        self.get_company(organization_id, company_id)
        return list(
            self.session.scalars(
                select(EstablishmentRecord).where(
                    EstablishmentRecord.organization_id == organization_id,
                    EstablishmentRecord.company_id == company_id,
                )
            )
        )

    def create_establishment(
        self, organization_id: str, company_id: str, now: datetime, **data: object
    ) -> EstablishmentRecord:
        self.get_company(organization_id, company_id)
        record = EstablishmentRecord(
            id=str(uuid4()),
            organization_id=organization_id,
            company_id=company_id,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
            **data,
        )
        self.session.add(record)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Establishment already exists in this organization") from exc
        return record

    def list_memberships(self, organization_id: str) -> list[dict[str, object]]:
        rows = self.session.execute(
            select(MembershipRecord, UserRecord)
            .join(UserRecord, UserRecord.id == MembershipRecord.user_id)
            .where(MembershipRecord.organization_id == organization_id)
            .order_by(UserRecord.display_name)
        )
        return [
            {
                "id": membership.id,
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": membership.role,
                "status": membership.status,
                "created_at": membership.created_at,
                "updated_at": membership.updated_at,
            }
            for membership, user in rows
        ]

    def update_membership(
        self,
        organization_id: str,
        membership_id: str,
        *,
        role: str | None,
        status: str | None,
        now: datetime,
    ) -> MembershipRecord:
        record = self.session.scalar(
            select(MembershipRecord).where(
                MembershipRecord.id == membership_id,
                MembershipRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise NotFoundError("Membership not found")
        if role is not None:
            record.role = role
        if status is not None:
            record.status = status
        record.updated_at = now
        self.session.flush()
        return record
