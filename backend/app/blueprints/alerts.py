"""Alerts controller: request reading and response shaping.

All logic (filters, SQL) lives in app/services/alert_service.py and
app/repositories/alert_repository.py.
"""

from quart import Blueprint, request

from app.security import require_auth
from app.services.alert_service import alert_service

bp = Blueprint("alerts", __name__)


@bp.get("")
@require_auth()
async def list_alerts():
    items = await alert_service.list(
        status=request.args.get("status"),
        severity=request.args.get("severity"),
        agent_id=request.args.get("agent_id", type=int),
        limit=request.args.get("limit", 100, type=int) or 100,
    )
    return {"items": items, "total": len(items)}
