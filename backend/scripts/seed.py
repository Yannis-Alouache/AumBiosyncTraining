"""Database seeding: a full realistic dataset or a minimal test dataset.

Usage:
    python -m scripts.seed              # full dataset into aumbiosync.db
    python -m scripts.seed --reset      # deletes the database before seeding

Dates are generated relative to "now": the week displayed in the console is
always the current week, including one ongoing night shift. The random
generator seed is fixed: two runs within the same minute produce the same
dataset. Domain data (names, professions, alert messages) stays French on
purpose: it is realistic product content for a French customer base.
"""

import argparse
import math
import os
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import create_engine_for, init_db
from app.models import Agent, Alert, Reading, Shift, Site, User
from app.security import hash_password

DEMO_PASSWORD = "OpsReady2026!"

EMAIL_DOMAINS = ["sdis21.fr", "chu-dijon.fr", "plastival.fr"]

SITES = [
    ("SDIS 21 - Centre d'incendie et de secours de Dijon", "SDIS", "Dijon"),
    ("CHU Dijon - Réanimation et unités de garde", "HOSPITAL", "Dijon"),
    ("Plastival Industries - Site de Mâcon", "INDUSTRY", "Mâcon"),
]

# (last_name, first_name, profession, grade, hire year)
AGENTS_PER_SITE = {
    0: [
        ("MOREAU", "Julien", "Pompier", "Sergent-chef", 2009),
        ("FERNANDEZ", "Alicia", "Pompier", "Caporal", 2014),
        ("GIRARD", "Thomas", "Pompier", "Sapeur", 2019),
        ("ROUSSEL", "Marine", "Pompier", "Lieutenant", 2011),
        ("BERTHIER", "Nicolas", "Pompier", "Caporal", 2016),
        ("LAMBERT", "Claire", "Infirmière sapeur-pompier", "Caporal", 2018),
        ("DUPUIS", "Alexandre", "Pompier", "Sapeur", 2021),
        ("CHEVALIER", "Sarah", "Pompier", "Sergent", 2013),
        ("MARCHAND", "Kevin", "Pompier", "Sapeur", 2022),
        ("FONTAINE", "Elodie", "Pompier", "Caporal", 2017),
    ],
    1: [
        ("BENALI", "Karim", "Personnel soignant", "Infirmier DE", 2015),
        ("NGUYEN", "Thao", "Personnel soignant", "Infirmière DE", 2019),
        ("PETIT", "Matthieu", "Personnel soignant", "Aide-soignant", 2020),
        ("ROBIN", "Camille", "Personnel soignant", "Infirmière DE", 2012),
        ("ADAM", "Sylvie", "Personnel soignant", "Aide-soignante", 2008),
        ("VIDAL", "Hugo", "Médecin garde", "Praticien", 2016),
        ("COLIN", "Julie", "Personnel soignant", "Infirmière DE", 2021),
        ("LEROY", "Antoine", "Personnel soignant", "Aide-soignant", 2023),
    ],
    2: [
        ("SAUNIER", "Marc", "Opérateur", "Conducteur d'installation", 2010),
        ("OLIVIER", "Nadia", "Opérateur", "Opératrice", 2018),
        ("BARBIER", "Yann", "Opérateur", "Chef d'équipe", 2007),
        ("RENAUD", "Sonia", "Opérateur", "Opératrice", 2021),
        ("LEGRAND", "Fabien", "Opérateur", "Opérateur", 2015),
        ("PERRIN", "Christelle", "Opérateur", "Opératrice", 2019),
    ],
}

USERS = [
    ("sofia.lambert@aum-bio.fr", "Lambert", "Sofia", "SUPERVISOR"),
    ("nadia.fournier@aum-bio.fr", "Fournier", "Nadia", "PLANNER"),
    ("admin@aum-bio.fr", "Support", "AUM", "ADMIN"),
]


def _status_for_period(starts_at: datetime, ends_at: datetime, reference: datetime) -> str:
    if reference >= ends_at:
        return "COMPLETED"
    if reference >= starts_at:
        return "IN_PROGRESS"
    return "SCHEDULED"


def _build_week_planning(
    agent_map: dict,
    site_objects: list[Site],
    monday: datetime,
    now: datetime,
) -> list[Shift]:
    """Current-week shifts for the three organisations, without overlap."""
    planning: list[Shift] = []

    def add(agent: Agent, shift_type: str, starts_at: datetime, ends_at: datetime, comment=None):
        if any(
            shift.agent is agent and shift.starts_at < ends_at.isoformat() and shift.ends_at > starts_at.isoformat()
            for shift in planning
        ):
            return
        planning.append(
            Shift(
                agent=agent,
                site=agent.site,
                type=shift_type,
                starts_at=starts_at.replace(microsecond=0).isoformat(),
                ends_at=ends_at.replace(microsecond=0).isoformat(),
                comment=comment,
            )
        )

    for site_idx in range(3):
        for i in range(len(AGENTS_PER_SITE[site_idx])):
            agent = agent_map[(site_idx, i)]
            if site_idx == 0:
                # Fire station: 24 h duty every 3 days, split into day + night.
                for d in range(7):
                    if (d + i * 2) % 3 == 0:
                        day = monday + timedelta(days=d)
                        duty_end = day + timedelta(days=1, hours=8)
                        if duty_end <= now:
                            add(agent, "DAY", day + timedelta(hours=8), day + timedelta(hours=20))
                            add(agent, "NIGHT", day + timedelta(hours=20), duty_end)
            elif site_idx == 1:
                # Hospital: 2 consecutive days then 1 rest day, alternating
                # day / night teams.
                for d in range(7):
                    if (d + i) % 3 in (0, 1):
                        day = monday + timedelta(days=d)
                        if i % 2 == 0:
                            add(agent, "DAY", day + timedelta(hours=7), day + timedelta(hours=19))
                        else:
                            add(agent, "NIGHT", day + timedelta(hours=19), day + timedelta(days=1, hours=7))
            else:
                # Factory 3x8: five days, one fixed shift per team this week.
                for d in range(5):
                    day = monday + timedelta(days=d)
                    slot = i % 3
                    if slot == 0:
                        add(agent, "DAY", day + timedelta(hours=6), day + timedelta(hours=14),
                            "Poste matin")
                    elif slot == 1:
                        add(agent, "DAY", day + timedelta(hours=14), day + timedelta(hours=22),
                            "Poste après-midi")
                    else:
                        add(agent, "NIGHT", day + timedelta(hours=22), day + timedelta(days=1, hours=6),
                            "Poste nuit")
                # The team leader carries the week-end on-call duty.
                if i == 2:
                    friday = monday + timedelta(days=4)
                    add(agent, "ON_CALL", friday + timedelta(hours=17),
                        monday + timedelta(days=7, hours=6), "Astreinte week-end")
    return planning


async def seed_database(database_path: str, dataset: str = "full") -> None:
    if dataset == "test":
        await _seed_test(database_path)
    else:
        await _seed_full(database_path)


async def _seed_full(database_path: str) -> None:
    rng = random.Random(42)
    now = datetime.now().replace(microsecond=0)
    monday = now.replace(hour=0, minute=0, second=0)
    monday -= timedelta(days=monday.weekday())

    engine = create_engine_for(database_path)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        sites = [Site(name=name, type=site_type, city=city) for name, site_type, city in SITES]
        session.add_all(sites)

        users = [
            User(email=email, last_name=last_name, first_name=first_name, role=role,
                 password_hash=hash_password(DEMO_PASSWORD))
            for email, last_name, first_name, role in USERS
        ]
        session.add_all(users)

        agent_map: dict = {}
        for site_idx, agents in AGENTS_PER_SITE.items():
            for i, (last_name, first_name, profession, grade, hire_year) in enumerate(agents):
                email = (
                    f"{first_name.lower()}.{last_name.lower().replace('-', '').replace(' ', '')}"
                    f"@{EMAIL_DOMAINS[site_idx]}"
                )
                agent = Agent(
                    site=sites[site_idx],
                    last_name=last_name,
                    first_name=first_name,
                    email=email,
                    profession=profession,
                    grade=grade,
                    hired_on=f"{hire_year}-09-01",
                )
                session.add(agent)
                agent_map[(site_idx, i)] = agent

        # Forced ongoing night shifts: three agents in a critical situation,
        # visible at any time of day in the console.
        forced_nights = [(0, 2), (1, 1), (2, 3)]
        ongoing_shifts = []
        for site_idx, i in forced_nights:
            forced_agent = agent_map[(site_idx, i)]
            shift = Shift(
                agent=forced_agent,
                site=forced_agent.site,
                type="NIGHT",
                starts_at=(now - timedelta(hours=5)).isoformat(),
                ends_at=(now + timedelta(hours=3)).isoformat(),
                status="IN_PROGRESS",
                predicted_fatigue_score=round(rng.uniform(78, 90), 1),
                comment="Nuit renforcée en cours",
            )
            session.add(shift)
            ongoing_shifts.append(shift)

        planning = _build_week_planning(agent_map, sites, monday, now)
        night_shift_by_agent: dict = {}
        for shift in planning:
            shift.status = _status_for_period(
                datetime.fromisoformat(shift.starts_at),
                datetime.fromisoformat(shift.ends_at),
                now,
            )
            bounds = {"DAY": (38, 60), "NIGHT": (62, 84), "ON_CALL": (25, 40)}[shift.type]
            shift.predicted_fatigue_score = round(rng.uniform(*bounds), 1)
            if shift.type == "NIGHT":
                night_shift_by_agent[shift.agent] = shift
        session.add_all(planning)

        # Current fatigue index of every agent, consistent with the ongoing
        # shift (week planning + forced night shifts).
        on_duty: dict = {}
        for shift in planning:
            if datetime.fromisoformat(shift.starts_at) <= now < datetime.fromisoformat(shift.ends_at):
                on_duty[shift.agent] = shift
        for shift in ongoing_shifts:
            on_duty[shift.agent] = shift
        for key, agent in agent_map.items():
            current_shift = on_duty.get(agent)
            if current_shift is not None and current_shift.type == "NIGHT":
                fatigue_index, sleep_hours = rng.uniform(74, 90), rng.uniform(4.5, 6.4)
            elif current_shift is not None:
                fatigue_index, sleep_hours = rng.uniform(46, 62), rng.uniform(6.8, 8.3)
            else:
                fatigue_index, sleep_hours = rng.uniform(12, 38), rng.uniform(6.5, 8.7)
            agent.fatigue_index = round(fatigue_index, 1)
            agent.last_sleep_hours = round(sleep_hours, 1)

        # Alerts: (site, agent, type, severity, message, hours before now, status, acknowledged)
        alerts = [
            ((0, 2), "FATIGUE_CRITICAL", "CRITICAL",
             "Indice de fatigue à 88/100 pendant la garde de nuit, confirmé par deux relevés Orbe consécutifs.",
             3, "NEW", False),
            ((1, 1), "INSUFFICIENT_RECOVERY", "WARNING",
             "Moins de 11 h de repos entre deux gardes de nuit consécutives.",
             26, "NEW", False),
            ((0, 4), "LOW_HRV", "WARNING",
             "HRV moyenne à 24 ms sur 24 h, sous le seuil individuel de 28 ms.",
             9, "NEW", False),
            ((2, 4), "OVERTIME", "INFO",
             "36 h effectuées cette semaine : quota du poste de nuit atteint.",
             31, "ACKNOWLEDGED", True),
            ((0, 0), "STAFFING_SHORTAGE", "CRITICAL",
             "Effectif de nuit insuffisant vendredi : 2 agents planifiés pour un minimum de 3.",
             5, "NEW", False),
            ((1, 3), "FATIGUE_CRITICAL", "CRITICAL",
             "Indice de fatigue à 81/100 et température à 37.9 degrés en fin de garde.",
             12, "NEW", False),
            ((1, 5), "INSUFFICIENT_RECOVERY", "WARNING",
             "Deuxième garde de nuit consécutive sans sieste enregistrée.",
             49, "ACKNOWLEDGED", True),
            ((0, 6), "LOW_HRV", "INFO",
             "HRV à 31 ms, en baisse de 18 % par rapport à la moyenne personnelle.",
             20, "NEW", False),
            ((2, 2), "OVERTIME", "INFO",
             "Astreinte du week-end dépassée : 3 interventions nocturnes.",
             2, "NEW", False),
            ((1, 0), "INSUFFICIENT_RECOVERY", "INFO",
             "Fin de garde à 7 h, reprise planifiée à 14 h le même jour.",
             40, "RESOLVED", False),
            ((0, 8), "STAFFING_SHORTAGE", "WARNING",
             "Agent en congé non remplacé sur le créneau d'astreinte de samedi.",
             15, "NEW", False),
            ((2, 0), "FATIGUE_CRITICAL", "CRITICAL",
             "Indice à 86/100 : conducteur d'installation en 3e nuit consécutive.",
             34, "ACKNOWLEDGED", True),
            ((1, 7), "LOW_HRV", "INFO",
             "HRV à 27 ms, sous la moyenne du service (34 ms).",
             6, "NEW", False),
            ((0, 3), "INSUFFICIENT_RECOVERY", "INFO",
             "Sieste de 40 min enregistrée après la garde de nuit de dimanche.",
             55, "ACKNOWLEDGED", True),
        ]
        supervisor = next(user for user in users if user.role == "SUPERVISOR")
        alert_objects = []
        for (site_idx, i), alert_type, severity, message, hours, status, acknowledged in alerts:
            agent = agent_map[(site_idx, i)]
            alert_objects.append(
                Alert(
                    agent=agent,
                    shift=night_shift_by_agent.get(agent),
                    type=alert_type,
                    severity=severity,
                    message=message,
                    status=status,
                    created_at=(now - timedelta(hours=hours)).isoformat(),
                    acknowledged_by_user=supervisor if acknowledged else None,
                    acknowledged_at=(now - timedelta(hours=hours - 1)).isoformat() if acknowledged else None,
                )
            )
        session.add_all(alert_objects)

        # Orbe readings: 48 hourly points per agent, circadian signals + noise.
        readings = []
        for key, agent in agent_map.items():
            agent_rng = random.Random(1000 + id(agent))
            ongoing_night = key in forced_nights
            high_fatigue = ongoing_night or agent_rng.random() < 0.2
            base_hr = 82 if high_fatigue else (72 if agent_rng.random() < 0.4 else 64)
            base_hrv = 22 if high_fatigue else (32 if agent_rng.random() < 0.4 else 52)
            for h in range(48, 0, -1):
                instant = now - timedelta(hours=h)
                phase = 2 * math.pi * (instant.hour - 3) / 24
                heart_rate = base_hr + 5 * math.sin(phase) + agent_rng.uniform(-3, 3)
                if ongoing_night and (instant.hour >= 22 or instant.hour <= 6):
                    heart_rate += 7
                hrv = max(8, base_hrv - 6 * math.sin(phase) + agent_rng.uniform(-4, 4))
                temperature = (
                    36.5 + (0.6 if high_fatigue else 0.15 * math.sin(phase)) + agent_rng.uniform(-0.15, 0.15)
                )
                readings.append(
                    Reading(
                        agent=agent,
                        recorded_at=instant.isoformat(),
                        heart_rate=int(heart_rate),
                        hrv=int(hrv),
                        temperature=round(temperature, 1),
                    )
                )
        session.add_all(readings)

        await session.commit()

    await engine.dispose()

    print(f"Database seeded: {len(sites)} sites, {len(agent_map)} agents, "
          f"{len(ongoing_shifts) + len(planning)} shifts, {len(alert_objects)} alerts, "
          f"{len(readings)} readings.")
    print(f"Demo accounts (password: {DEMO_PASSWORD}):")
    for user in users:
        print(f"  {user.email} ({user.role})")


async def _seed_test(database_path: str) -> None:
    """Minimal deterministic dataset for the pytest suite."""
    now = datetime.now().replace(microsecond=0)

    engine = create_engine_for(database_path)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        site = Site(name="SDIS 21 - CSI Test", type="SDIS", city="Dijon")
        session.add(site)

        users = [
            User(email=email, last_name=last_name, first_name=first_name, role=role,
                 password_hash=hash_password(DEMO_PASSWORD))
            for email, last_name, first_name, role in USERS
        ]
        session.add_all(users)

        agents = [
            ("MOREAU", "Julie", 30.0, 8.0),
            ("BERNARD", "Paul", 55.0, 6.5),
            ("DARCY", "Eva", 88.0, 4.0),
        ]
        agent_objects = []
        for last_name, first_name, fatigue_index, sleep_hours in agents:
            agent = Agent(
                site=site,
                last_name=last_name,
                first_name=first_name,
                email=f"{first_name.lower()}.{last_name.lower()}@test.aum-bio.fr",
                profession="Pompier",
                grade="Sapeur",
                fatigue_index=fatigue_index,
                last_sleep_hours=sleep_hours,
                hired_on="2020-01-01",
            )
            session.add(agent)
            agent_objects.append(agent)

        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        in_three_days = (now + timedelta(days=3)).replace(hour=0, minute=0, second=0)
        shifts = [
            Shift(agent=agent_objects[1], site=site, type="DAY",
                  starts_at=(tomorrow + timedelta(hours=8)).isoformat(),
                  ends_at=(tomorrow + timedelta(hours=20)).isoformat(),
                  status="SCHEDULED", predicted_fatigue_score=52.0),
            Shift(agent=agent_objects[2], site=site, type="NIGHT",
                  starts_at=(now - timedelta(hours=2)).isoformat(),
                  ends_at=(now + timedelta(hours=6)).isoformat(),
                  status="IN_PROGRESS", predicted_fatigue_score=84.0),
            Shift(agent=agent_objects[0], site=site, type="DAY",
                  starts_at=(in_three_days + timedelta(hours=8)).isoformat(),
                  ends_at=(in_three_days + timedelta(hours=20)).isoformat(),
                  status="SCHEDULED", predicted_fatigue_score=41.0),
        ]
        session.add_all(shifts)

        session.add(
            Alert(agent=agent_objects[2], type="FATIGUE_CRITICAL", severity="CRITICAL",
                  message="Indice de fatigue à 88/100 pendant la garde de nuit.",
                  status="NEW", created_at=(now - timedelta(hours=2)).isoformat())
        )
        session.add(
            Alert(agent=agent_objects[1], type="LOW_HRV", severity="WARNING",
                  message="HRV moyenne à 24 ms sur 24 h.",
                  status="ACKNOWLEDGED", created_at=(now - timedelta(hours=10)).isoformat(),
                  acknowledged_by_user=users[0],
                  acknowledged_at=(now - timedelta(hours=9)).isoformat())
        )

        for agent, (heart_rate, hrv) in zip(agent_objects, [(64, 52), (74, 34), (86, 20)]):
            for h in (3, 2, 1):
                session.add(
                    Reading(agent=agent, recorded_at=(now - timedelta(hours=h)).isoformat(),
                            heart_rate=heart_rate, hrv=hrv, temperature=36.7)
                )

        await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the OpsReady console database.")
    parser.add_argument("--reset", action="store_true", help="Deletes the database before seeding")
    parser.add_argument("--path", default=None, help="SQLite file path")
    args = parser.parse_args()

    import asyncio

    from app.config import Config

    database_path = args.path or Config.DATABASE
    if args.reset and os.path.exists(database_path):
        os.remove(database_path)
        print(f"Existing database deleted: {database_path}")

    asyncio.run(init_db(database_path))
    asyncio.run(seed_database(database_path, dataset="full"))
