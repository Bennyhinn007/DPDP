from flask import Blueprint

compliance_bp = Blueprint("compliance", __name__)

from app.blueprints.compliance import routes  # noqa: E402, F401
