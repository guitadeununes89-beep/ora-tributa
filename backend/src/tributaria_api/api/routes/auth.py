from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from tributaria_api.api.auth_dependencies import (
    AuthenticationServiceDep,
    CorrelationId,
    CsrfAuthContext,
    CurrentAuthContext,
)
from tributaria_api.config import get_settings
from tributaria_api.contracts.identity import CurrentUserView, LoginRequest

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=CurrentUserView)
def login(
    request: LoginRequest,
    response: Response,
    service: AuthenticationServiceDep,
    correlation_id: CorrelationId,
) -> dict[str, object]:
    session_token, csrf_token, context = service.login(
        request.email, request.password, request.organization_slug, correlation_id
    )
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return context_view(context)


@router.get("/me", response_model=CurrentUserView)
def me(context: CurrentAuthContext) -> dict[str, object]:
    return context_view(context)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    service: AuthenticationServiceDep,
    _context: CsrfAuthContext,
    session_token: Annotated[str | None, Cookie(alias="tributaria_session")] = None,
) -> None:
    service.logout(session_token)
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    response.delete_cookie(get_settings().csrf_cookie_name, path="/")


def context_view(context: object) -> dict[str, object]:
    value = context
    return {
        "user_id": value.user_id,  # type: ignore[attr-defined]
        "email": value.email,  # type: ignore[attr-defined]
        "display_name": value.display_name,  # type: ignore[attr-defined]
        "organization_id": value.organization_id,  # type: ignore[attr-defined]
        "organization_name": value.organization_name,  # type: ignore[attr-defined]
        "membership_id": value.membership_id,  # type: ignore[attr-defined]
        "role": value.role,  # type: ignore[attr-defined]
        "permissions": sorted(value.permissions),  # type: ignore[attr-defined]
    }
