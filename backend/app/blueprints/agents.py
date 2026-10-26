"""Agents controller: request reading and response shaping.

All logic (filters, SQL) lives in app/services/agent_service.py and
app/repositories/agent_repository.py.
"""

from quart import Blueprint, request

from app.security import require_auth
from app.services.agent_service import agent_service

bp = Blueprint("agents", __name__)


@bp.get("")
@require_auth()
async def list_agents():
    items = await agent_service.list(
        q=request.args.get("q"),
        site_id=request.args.get("site_id", type=int),
        status=request.args.get("status"),
    )
    return {"items": items, "total": len(items)}
