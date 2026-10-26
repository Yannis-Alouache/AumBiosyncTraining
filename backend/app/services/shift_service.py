"""Shifts (duties and on-call stints) business logic: paginated planning.

Roadmap (TICKETS.md, tickets T02, T09 and T10): scheduling, update and
deletion extend this service — their business rules (no overlapping
shifts, minimal rest between two shifts) belong here, not in the
blueprint.
"""

from app.repositories.shift_repository import shift_repository

DEFAULT_PAGE_SIZE = 200
MAX_PAGE_SIZE = 200


class ShiftService:
    async def list(
        self,
        site_id: int | None = None,
        agent_id: int | None = None,
        status: str | None = None,
        from_day: str | None = None,
        to_day: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict:
        """Business rules owned here: page bounds and response shape.
        Query composition and pagination live in the repository."""
        page = max(1, page)
        page_size = min(MAX_PAGE_SIZE, max(1, page_size))

        items, total = await shift_repository.list(
            site_id=site_id,
            agent_id=agent_id,
            status=status,
            from_day=from_day,
            to_day=to_day,
            page=page,
            page_size=page_size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-total // page_size)),
        }


shift_service = ShiftService()
