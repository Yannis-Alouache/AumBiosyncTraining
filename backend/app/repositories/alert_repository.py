"""Repository for fatigue alerts."""

from sqlalchemy import select

from app.db import get_session
from app.models import Agent, Alert, User


class AlertRepository:
    """ORM access to the alerts table, joined with agents and users."""

    async def list(
        self,
        status: str | None = None,
        severity: str | None = None,
        agent_id: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Most recent alerts first, filtered by status, severity and agent."""
        session = await get_session()
        statement = (
            select(Alert, Agent, User)
            .join(Agent, Alert.agent_id == Agent.id)
            .outerjoin(User, Alert.acknowledged_by == User.id)
        )
        if status:
            statement = statement.where(Alert.status == status)
        if severity:
            statement = statement.where(Alert.severity == severity)
        if agent_id is not None:
            statement = statement.where(Alert.agent_id == agent_id)
        statement = statement.order_by(Alert.created_at.desc()).limit(limit)

        rows = (await session.execute(statement)).all()
        return [self._to_dict(alert, agent, user) for alert, agent, user in rows]

    def _to_dict(self, alert: Alert, agent: Agent, user: User | None) -> dict:
        return {
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "status": alert.status,
            "created_at": alert.created_at,
            "acknowledged_at": alert.acknowledged_at,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_by_name": user.last_name if user is not None else None,
            "agent_id": alert.agent_id,
            "shift_id": alert.shift_id,
            "agent_last_name": agent.last_name,
            "agent_first_name": agent.first_name,
        }


alert_repository = AlertRepository()
