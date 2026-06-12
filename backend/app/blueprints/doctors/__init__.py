from flask import Blueprint

doctors_bp = Blueprint("doctors", __name__)

from app.blueprints.doctors import routes  # noqa: E402, F401
