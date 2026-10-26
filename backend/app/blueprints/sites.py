"""Sites controller: request reading and response shaping."""

from quart import Blueprint

from app.security import require_auth
from app.services.site_service import site_service

bp = Blueprint("sites", __name__)


@bp.get("")
@require_auth()
async def list_sites():
    return {"items": await site_service.list()}
