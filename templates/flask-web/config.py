import os


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-not-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///instance/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


CONFIGS = {"default": Config, "testing": TestingConfig}
