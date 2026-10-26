"""Request body helpers."""

from quart import request

from app.errors import ApiError


async def json_body() -> dict:
    """Returns the request JSON body, or raises an explicit 422 error."""
    body = await request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError(422, "INVALID_BODY", "Corps de requête JSON attendu")
    return body
