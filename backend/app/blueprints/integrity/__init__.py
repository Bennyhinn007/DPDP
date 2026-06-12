from flask import Blueprint

integrity_bp = Blueprint("integrity", __name__)

from app.blueprints.integrity import routes  # noqa: E402, F401
