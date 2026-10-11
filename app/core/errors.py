from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings

PROBLEM_MEDIA_TYPE = "application/problem+json"
_PROBLEM_TYPE_BASE = "https://cyber-implant-cloud.local/problems"
_UNPROCESSABLE = 422


class DomainError(Exception):
    """Base for failures that map onto a defined HTTP response.

    Services raise these instead of HTTPException so business logic stays free
    of transport concerns and is reusable from scripts and tests.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    problem_type: str = "internal-error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str, **extra: Any) -> None:
        super().__init__(detail)
        self.detail = detail
        self.extra = extra


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    problem_type = "resource-not-found"
    title = "Resource Not Found"


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    problem_type = "state-conflict"
    title = "Conflicting Resource State"


class UnauthorizedError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    problem_type = "authentication-required"
    title = "Authentication Required"


class ForbiddenError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    problem_type = "access-denied"
    title = "Access Denied"


class UnprocessableError(DomainError):
    status_code = _UNPROCESSABLE
    problem_type = "business-rule-violation"
    title = "Business Rule Violation"


def _serialisable_errors(exc: RequestValidationError) -> Any:
    """Render Pydantic's error list as JSON, dropping the non-encodable ctx object."""
    cleaned = []
    for error in exc.errors():
        entry = {key: value for key, value in error.items() if key != "ctx"}
        context = error.get("ctx")
        if context:
            entry["ctx"] = {key: str(value) for key, value in context.items()}
        cleaned.append(entry)
    return jsonable_encoder(cleaned)


def problem_response(
    request: Request,
    *,
    status_code: int,
    problem_type: str,
    title: str,
    detail: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build an RFC 9457 application/problem+json response."""
    body: dict[str, Any] = {
        "type": f"{_PROBLEM_TYPE_BASE}/{problem_type}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body, media_type=PROBLEM_MEDIA_TYPE)


_STARLETTE_PROBLEM_TITLES = {
    status.HTTP_401_UNAUTHORIZED: ("authentication-required", "Authentication Required"),
    status.HTTP_403_FORBIDDEN: ("access-denied", "Access Denied"),
    status.HTTP_404_NOT_FOUND: ("resource-not-found", "Resource Not Found"),
    status.HTTP_405_METHOD_NOT_ALLOWED: ("method-not-allowed", "Method Not Allowed"),
}


def register_exception_handlers(app: FastAPI) -> None:
    """Route every failure mode through one problem+json shape."""

    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return problem_response(
            request,
            status_code=exc.status_code,
            problem_type=exc.problem_type,
            title=exc.title,
            detail=exc.detail,
            extra=exc.extra or None,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return problem_response(
            request,
            status_code=_UNPROCESSABLE,
            problem_type="request-validation-failed",
            title="Request Validation Failed",
            detail="One or more request parameters are invalid.",
            extra={"errors": _serialisable_errors(exc)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        problem_type, title = _STARLETTE_PROBLEM_TITLES.get(
            exc.status_code, ("http-error", "HTTP Error")
        )
        return problem_response(
            request,
            status_code=exc.status_code,
            problem_type=problem_type,
            title=title,
            detail=str(exc.detail),
        )

    # Lab3: in production (DEBUG=False) an unhandled error must not leak internals;
    # in development the real message is surfaced to aid debugging.
    @app.exception_handler(Exception)
    async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        debug = get_settings().debug
        detail = str(exc) if debug else "An internal error occurred."
        extra = {"exception": type(exc).__name__} if debug else None
        return problem_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            problem_type="internal-error",
            title="Internal Server Error",
            detail=detail,
            extra=extra,
        )
