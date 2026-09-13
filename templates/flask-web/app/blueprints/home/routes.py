from flask import Blueprint, render_template, request

from app.services.greeting import greeting

bp = Blueprint("home", __name__)


@bp.get("/")
def index():
    template = "partials/greeting.html" if request.headers.get("HX-Request") else "home/index.html"
    return render_template(template, message=greeting())
