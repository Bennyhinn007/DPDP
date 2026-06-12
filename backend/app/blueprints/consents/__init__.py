from flask import Blueprint

consents_bp = Blueprint("consents", __name__)

from app.blueprints.consents import routes  # noqa: E402, F401
