from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from tributaria_api.application.authentication import AuthenticationService, token_hash
from tributaria_api.application.security import AuthContext, Permission
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.identity_repository import IdentityRepository
from tributaria_api.infrastructure.database.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_identity_repository(session: SessionDep) -> IdentityRepository:
    return IdentityRepository(session)


IdentityRepositoryDep = Annotated[IdentityRepository, Depends(get_identity_repository)]


def get_authentication_service(repository: IdentityRepositoryDep) -> AuthenticationService:
    return AuthenticationService(repository, get_settings().session_ttl_seconds)


AuthenticationServiceDep = Annotated[AuthenticationService, Depends(get_authentication_service)]


def current_auth_context(
    service: AuthenticationServiceDep,
    session_token: Annotated[str | None, Cookie(alias="tributaria_session")] = None,
) -> AuthContext:
    context, _ = service.authenticate(session_token)
    return context


CurrentAuthContext = Annotated[AuthContext, Depends(current_auth_context)]


def require_csrf(
    request: Request,
    service: AuthenticationServiceDep,
    session_token: Annotated[str | None, Cookie(alias="tributaria_session")] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias="tributaria_csrf")] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> AuthContext:
    context, expected_hash = service.authenticate(session_token)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
        if not secrets_compare(token_hash(csrf_header), expected_hash):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
    return context


def secrets_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)


CsrfAuthContext = Annotated[AuthContext, Depends(require_csrf)]


def correlation_id(value: Annotated[str | None, Header(alias="X-Correlation-ID")] = None) -> str:
    return value or str(uuid4())


CorrelationId = Annotated[str, Depends(correlation_id)]


def require_permission(permission: Permission):  # type: ignore[no-untyped-def]
    def dependency(context: CsrfAuthContext) -> AuthContext:
        context.require(permission)
        return context

    return dependency


ReadContext = Annotated[AuthContext, Depends(require_permission(Permission.READ))]
AnalystContext = Annotated[AuthContext, Depends(require_permission(Permission.RUN_EVALUATION))]
CuratorContext = Annotated[AuthContext, Depends(require_permission(Permission.CURATE_RULE))]
ApproverContext = Annotated[AuthContext, Depends(require_permission(Permission.APPROVE_RULE))]
PublisherContext = Annotated[AuthContext, Depends(require_permission(Permission.PUBLISH_RULE))]
CompanyManagerContext = Annotated[
    AuthContext, Depends(require_permission(Permission.MANAGE_COMPANY))
]
MembershipManagerContext = Annotated[
    AuthContext, Depends(require_permission(Permission.MANAGE_MEMBERSHIP))
]
