from flask import Blueprint

pharmacy_bp = Blueprint("pharmacy", __name__)

from app.blueprints.pharmacy import routes  # noqa: E402, F401
