"""OpsReady Console by AUM-Biosync: Quart API.

Application factory: assembles configuration, the SQLAlchemy async engine,
the API blueprints and the error handlers.
"""

from quart import Quart
from quart_cors import cors

from app.config import Config
from app.db import bind_engine, close_db, init_db
from app.errors import register_error_handlers

VERSION = "1.2.0"


def create_app(config: Config | None = None) -> Quart:
    app = Quart(__name__)
    app.config.from_object(Config)
    if config is not None:
        app.config.from_object(config)

    app = cors(
        app,
        allow_origin=app.config["CORS_ORIGINS"],
        allow_credentials=True,
    )

    bind_engine(app)

    @app.before_serving
    async def prepare_database():
        await init_db(app.config["DATABASE"])

    from app.blueprints import register_blueprints

    register_blueprints(app)
    register_error_handlers(app)
    app.teardown_appcontext(close_db)

    @app.get("/api/health")
    async def health():
        """Liveness probe, no authentication."""
        return {"status": "ok", "service": "opsready-console", "version": VERSION}

    return app
