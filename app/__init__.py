import os
from flask import Flask

from .models import close_db, init_db


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "agriconnect-secret-key"),
        DATABASE=os.environ.get(
            "AGRICONNECT_DB",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "agriconnect.db"),
        ),
    )

    if test_config:
        app.config.update(test_config)

    from .routes import main

    app.register_blueprint(main)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    return app
