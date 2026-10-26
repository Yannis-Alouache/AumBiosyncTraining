"""API configuration, overridable through AUM_* environment variables."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get(
        "AUM_SECRET_KEY", "dev-secret-a-changer-en-production-0123456789abcdef"
    )
    DATABASE = os.environ.get("AUM_DATABASE", str(BASE_DIR / "aumbiosync.db"))
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 8
    # Origins allowed for the development front-end.
    CORS_ORIGINS = ["http://localhost:4200", "http://127.0.0.1:4200"]
