import os
import secrets
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .models import close_db, init_db

csrf = CSRFProtect()


def _environment_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_environment_flag("SESSION_COOKIE_SECURE"),
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=3600,
        DATABASE=os.environ.get(
            "AGRICONNECT_DB",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "agriconnect.db"),
        ),
    )

    if test_config:
        app.config.update(test_config)

    from .routes import main

    app.register_blueprint(main)
    csrf.init_app(app)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    return app
