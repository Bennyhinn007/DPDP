"""Pharmacy blueprint routes — implemented in Week 2."""

from app.blueprints.pharmacy import pharmacy_bp


@pharmacy_bp.route("/health", methods=["GET"])
def pharmacy_health():
    return {"status": "pharmacy service ready"}, 200
