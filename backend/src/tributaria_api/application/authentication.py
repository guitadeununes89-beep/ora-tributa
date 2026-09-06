from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from tributaria_api.application.errors import AuthenticationError
from tributaria_api.application.security import AuthContext, Role
from tributaria_api.infrastructure.database.identity_models import (
    AuthSessionRecord,
    MembershipRecord,
    OrganizationRecord,
    UserCredentialRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.identity_repository import IdentityRepository

AuthRow = tuple[UserRecord, UserCredentialRecord | None, OrganizationRecord, MembershipRecord]

LoginRow = tuple[UserRecord, UserCredentialRecord, OrganizationRecord, MembershipRecord]


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AuthenticationService:
    def __init__(self, repository: IdentityRepository, ttl_seconds: int) -> None:
        self.repository = repository
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hasher = PasswordHasher()
        self._dummy_hash = self.hasher.hash("invalid-credential-placeholder")

    def login(
        self, email: str, password: str, organization_slug: str, correlation_id: str
    ) -> tuple[str, str, AuthContext]:
        candidate = self.repository.login_candidate(email, organization_slug)
        password_hash = candidate[1].password_hash if candidate else self._dummy_hash
        valid: bool
        try:
            valid = self.hasher.verify(password_hash, password)
        except VerificationError:
            valid = False
        if candidate is None or not valid:
            raise AuthenticationError("Invalid credentials")
        typed_candidate = cast(AuthRow, candidate)
        user, _, organization, membership = typed_candidate
        now = datetime.now(UTC)
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        session_id = str(uuid4())
        self.repository.create_session(
            id=session_id,
            user_id=user.id,
            organization_id=organization.id,
            membership_id=membership.id,
            token_hash=token_hash(session_token),
            csrf_hash=token_hash(csrf_token),
            created_at=now,
            expires_at=now + self.ttl,
            last_seen_at=now,
            revoked_at=None,
        )
        user.last_login_at = now
        self.repository.record_audit(
            organization_id=organization.id,
            user_id=user.id,
            entity_type="auth_session",
            entity_id=session_id,
            action="LOGIN_SUCCEEDED",
            occurred_at=now,
            correlation_id=correlation_id,
        )
        self.repository.session.commit()
        return session_token, csrf_token, self._context(typed_candidate, session_id)

    def authenticate(self, session_token: str | None) -> tuple[AuthContext, str]:
        if not session_token:
            raise AuthenticationError("Authentication required")
        row = self.repository.resolve_session(token_hash(session_token), datetime.now(UTC))
        if row is None:
            raise AuthenticationError("Authentication required")
        typed_row = cast(
            tuple[AuthSessionRecord, UserRecord, OrganizationRecord, MembershipRecord], row
        )
        session, user, organization, membership = typed_row
        return self._context(
            (user, cast(UserCredentialRecord, None), organization, membership), session.id
        ), session.csrf_hash

    def logout(self, session_token: str | None) -> None:
        if session_token:
            self.repository.revoke_session(token_hash(session_token), datetime.now(UTC))

    @staticmethod
    def _context(row: AuthRow, session_id: str) -> AuthContext:
        user, _, organization, membership = row
        return AuthContext(
            session_id=session_id,
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            organization_id=organization.id,
            organization_name=organization.name,
            membership_id=membership.id,
            role=Role(membership.role),
        )
