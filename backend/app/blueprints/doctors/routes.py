"""Doctors blueprint routes — implemented in Week 2."""

from app.blueprints.doctors import doctors_bp


@doctors_bp.route("/health", methods=["GET"])
def doctors_health():
    return {"status": "doctors service ready"}, 200
