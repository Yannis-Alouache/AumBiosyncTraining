from quart import Quart


def register_blueprints(app: Quart) -> None:
    from app.blueprints.alerts import bp as alerts_bp
    from app.blueprints.agents import bp as agents_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.sites import bp as sites_bp
    from app.blueprints.shifts import bp as shifts_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(sites_bp, url_prefix="/api/sites")
    app.register_blueprint(agents_bp, url_prefix="/api/agents")
    app.register_blueprint(shifts_bp, url_prefix="/api/shifts")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
