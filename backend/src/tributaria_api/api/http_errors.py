from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from tributaria_api.application.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    GovernanceError,
    NotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    def response(code: str, detail: str, status_code: int) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"code": code, "detail": detail})

    @app.exception_handler(AuthenticationError)
    async def authentication(_: Request, exc: AuthenticationError) -> JSONResponse:
        return response("AUTHENTICATION_REQUIRED", str(exc), status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(AuthorizationError)
    async def authorization(_: Request, exc: AuthorizationError) -> JSONResponse:
        return response("FORBIDDEN", str(exc), status.HTTP_403_FORBIDDEN)

    @app.exception_handler(NotFoundError)
    async def not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return response("NOT_FOUND", str(exc), status.HTTP_404_NOT_FOUND)

    @app.exception_handler(ConflictError)
    async def conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return response("CONFLICT", str(exc), status.HTTP_409_CONFLICT)

    @app.exception_handler(GovernanceError)
    async def governance(_: Request, exc: GovernanceError) -> JSONResponse:
        return response("GOVERNANCE_INVARIANT", str(exc), status.HTTP_422_UNPROCESSABLE_ENTITY)
