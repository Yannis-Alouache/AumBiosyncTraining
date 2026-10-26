"""Business errors and the stable error response shape used across the API.

Every error returned to the client has the form:
    {"error": {"code": "...", "message": "...", "details": ...}}

Codes are English identifiers (machine-facing); messages stay French
(user-facing, displayed in the console).
"""

import logging

from pydantic import ValidationError
from quart import Quart, jsonify

log = logging.getLogger("opsready")


class ApiError(Exception):
    """Business error: raised in services, converted to a JSON response."""

    def __init__(self, status: int, code: str, message: str, details: dict | list | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def error_response(status: int, code: str, message: str, details: dict | list | None = None):
    return (
        jsonify({"error": {"code": code, "message": message, "details": details}}),
        status,
    )


def register_error_handlers(app: Quart) -> None:
    @app.errorhandler(ApiError)
    async def _api_error(err: ApiError):
        return error_response(err.status, err.code, err.message, err.details)

    @app.errorhandler(ValidationError)
    async def _validation(err: ValidationError):
        details = [
            {"field": ".".join(str(n) for n in e["loc"]), "message": e["msg"]}
            for e in err.errors()
        ]
        return error_response(422, "VALIDATION", "Données invalides", details)

    @app.errorhandler(404)
    async def _not_found(_err):
        return error_response(404, "NOT_FOUND", "Ressource inconnue")

    @app.errorhandler(405)
    async def _method_not_allowed(_err):
        return error_response(405, "METHOD_NOT_ALLOWED", "Méthode non autorisée sur cette route")

    @app.errorhandler(Exception)
    async def _unexpected(err: Exception):
        log.exception("Unhandled error: %s", err)
        return error_response(500, "INTERNAL_ERROR", "Une erreur interne est survenue")
