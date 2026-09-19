"""
Centralised error handling for the Fitness OptiMax API.

Every failure that reaches the client should carry a human-readable `detail`
so the UI (and the Cloud Run logs) explain *what* broke instead of a bare 500.
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("optimax")


class OptiMaxError(Exception):
    """Base class for errors we raise deliberately and can explain to the user."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, hint: str | None = None, cause: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.cause = cause

    def to_payload(self) -> dict:
        payload = {"detail": self.message, "code": self.code}
        if self.hint:
            payload["hint"] = self.hint
        return payload


class BigQueryAuthError(OptiMaxError):
    """The service could not authenticate to BigQuery at all."""

    status_code = 503
    code = "bigquery_auth"


class BigQueryQueryError(OptiMaxError):
    """BigQuery rejected or failed the query."""

    status_code = 502
    code = "bigquery_query"


class DriveScopeError(BigQueryQueryError):
    """BigQuery could not read the Google Sheets-backed external table."""

    code = "drive_scope"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(OptiMaxError)
    async def optimax_error_handler(request: Request, exc: OptiMaxError):
        logger.error(
            "%s on %s: %s", exc.code, request.url.path, exc.message,
            exc_info=exc.cause or exc,
        )
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        # Without this, FastAPI returns a bare "Internal Server Error" body and
        # the browser only ever sees "500" — which is what made this hard to debug.
        logger.error(
            "Unhandled %s on %s: %s\n%s",
            type(exc).__name__, request.url.path, exc, traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"{type(exc).__name__}: {exc}",
                "code": "internal_error",
                "hint": "Full traceback is in the Cloud Run logs. Try /api/diagnostics.",
            },
        )
