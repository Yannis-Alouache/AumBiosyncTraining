"""SQLAlchemy ORM models: the single source of truth for the schema.

Convention: timestamps are stored as local naive ISO 8601 strings (no
timezone), which sort lexicographically. This is a deliberate
simplification for this demo database; see README.
"""

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    type: Mapped[str] = mapped_column(String(16))  # SDIS | HOSPITAL | INDUSTRY
    city: Mapped[str] = mapped_column(String(80))

    agents: Mapped[list["Agent"]] = relationship(back_populates="site")


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'LEAVE', 'TRAINING', 'SUSPENDED')",
            name="ck_agents_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    last_name: Mapped[str] = mapped_column(String(80))
    first_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    profession: Mapped[str] = mapped_column(String(80))
    grade: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    fatigue_index: Mapped[float] = mapped_column(Float, default=0.0)
    last_sleep_hours: Mapped[float | None] = mapped_column(Float)
    hired_on: Mapped[str] = mapped_column(String(10))  # ISO date

    site: Mapped["Site"] = relationship(back_populates="agents")
    shifts: Mapped[list["Shift"]] = relationship(back_populates="agent")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="agent")
    readings: Mapped[list["Reading"]] = relationship(back_populates="agent")


class Shift(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        CheckConstraint("type IN ('DAY', 'NIGHT', 'ON_CALL')", name="ck_shifts_type"),
        CheckConstraint(
            "status IN ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="ck_shifts_status",
        ),
        Index("idx_shifts_agent", "agent_id", "starts_at"),
        Index("idx_shifts_start", "starts_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    type: Mapped[str] = mapped_column(String(16))  # DAY | NIGHT | ON_CALL
    starts_at: Mapped[str] = mapped_column(String(19))  # ISO local naive
    ends_at: Mapped[str] = mapped_column(String(19))
    status: Mapped[str] = mapped_column(String(16), default="SCHEDULED")
    predicted_fatigue_score: Mapped[float | None] = mapped_column(Float)
    comment: Mapped[str | None] = mapped_column(String(500))

    agent: Mapped["Agent"] = relationship(back_populates="shifts")
    site: Mapped["Site"] = relationship()


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint("severity IN ('INFO', 'WARNING', 'CRITICAL')", name="ck_alerts_severity"),
        CheckConstraint(
            "status IN ('NEW', 'ACKNOWLEDGED', 'RESOLVED')",
            name="ck_alerts_status",
        ),
        Index("idx_alerts_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id"))
    type: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="NEW")
    created_at: Mapped[str] = mapped_column(String(19))
    acknowledged_by: Mapped[int | None] = mapped_column(
        "acknowledged_by", ForeignKey("users.id")
    )
    acknowledged_at: Mapped[str | None] = mapped_column(String(19))

    agent: Mapped["Agent"] = relationship(back_populates="alerts")
    shift: Mapped["Shift"] = relationship()
    acknowledged_by_user: Mapped["User"] = relationship()


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        Index("idx_readings_agent", "agent_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    recorded_at: Mapped[str] = mapped_column(String(19))
    heart_rate: Mapped[int] = mapped_column(Integer)
    hrv: Mapped[int] = mapped_column(Integer)
    temperature: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="ORBE_V2")

    agent: Mapped["Agent"] = relationship(back_populates="readings")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('SUPERVISOR', 'PLANNER', 'ADMIN')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(160), unique=True)
    last_name: Mapped[str] = mapped_column(String(80))
    first_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(16))
    password_hash: Mapped[str] = mapped_column(String(255))
