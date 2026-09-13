from flask import Flask, jsonify

from app.models import db
from app.wsgi_prefix import ForwardedPrefix


def create_app(config_name: str = "default") -> Flask:
    from config import CONFIGS

    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name])
    db.init_app(app)

    from app.blueprints.home.routes import bp as home_bp

    app.register_blueprint(home_bp)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    app.wsgi_app = ForwardedPrefix(app.wsgi_app)
    return app
