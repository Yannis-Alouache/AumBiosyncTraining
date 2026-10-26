"""Shifts controller: request reading and response shaping.

All logic (filters, pagination, SQL) lives in app/services/shift_service.py
and app/repositories/shift_repository.py.
"""

from quart import Blueprint, request

from app.security import require_auth
from app.services.shift_service import shift_service

bp = Blueprint("shifts", __name__)


@bp.get("")
@require_auth()
async def list_shifts():
    return await shift_service.list(
        site_id=request.args.get("site_id", type=int),
        agent_id=request.args.get("agent_id", type=int),
        status=request.args.get("status"),
        from_day=request.args.get("from"),
        to_day=request.args.get("to"),
        page=request.args.get("page", 1, type=int) or 1,
        page_size=request.args.get("page_size", 200, type=int) or 200,
    )
