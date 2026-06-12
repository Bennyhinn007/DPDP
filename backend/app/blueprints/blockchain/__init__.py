from flask import Blueprint

blockchain_bp = Blueprint("blockchain", __name__)

from app.blueprints.blockchain import routes  # noqa: E402, F401
