"""Repository for shifts (duties and on-call stints)."""

from sqlalchemy import func, select

from app.db import get_session
from app.models import Agent, Shift, Site


class ShiftRepository:
    """ORM access to the shifts table, joined with agents and sites.

    The service decides *what* is filterable (typed parameters); this
    class decides *how* the query is composed and paginated.
    """

    async def list(
        self,
        site_id: int | None = None,
        agent_id: int | None = None,
        status: str | None = None,
        from_day: str | None = None,
        to_day: str | None = None,
        page: int = 1,
        page_size: int = 200,
    ) -> tuple[list[dict], int]:
        """Chronologically ordered page of shifts, with the total count."""
        session = await get_session()
        conditions = []
        if site_id is not None:
            conditions.append(Shift.site_id == site_id)
        if agent_id is not None:
            conditions.append(Shift.agent_id == agent_id)
        if status:
            conditions.append(Shift.status == status)
        if from_day:
            conditions.append(Shift.starts_at >= f"{from_day}T00:00:00")
        if to_day:
            conditions.append(Shift.starts_at <= f"{to_day}T23:59:59")

        total = await session.scalar(
            select(func.count()).select_from(Shift).where(*conditions)
        )
        statement = (
            select(Shift, Agent, Site)
            .join(Agent, Shift.agent_id == Agent.id)
            .join(Site, Shift.site_id == Site.id)
            .where(*conditions)
            .order_by(Shift.starts_at)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await session.execute(statement)).all()
        items = [self._to_dict(shift, agent, site) for shift, agent, site in rows]
        return items, total or 0

    def _to_dict(self, shift: Shift, agent: Agent, site: Site) -> dict:
        return {
            "id": shift.id,
            "type": shift.type,
            "starts_at": shift.starts_at,
            "ends_at": shift.ends_at,
            "status": shift.status,
            "predicted_fatigue_score": shift.predicted_fatigue_score,
            "comment": shift.comment,
            "agent_id": shift.agent_id,
            "site_id": shift.site_id,
            "agent_last_name": agent.last_name,
            "agent_first_name": agent.first_name,
            "agent_profession": agent.profession,
            "site_name": site.name,
        }


shift_repository = ShiftRepository()
