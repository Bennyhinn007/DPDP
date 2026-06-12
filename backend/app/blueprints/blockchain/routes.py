"""
Blockchain Blueprint Routes.

Provides blockchain status and anchor lookup endpoints.
"""

from flask import jsonify, g

from app.blueprints.blockchain import blockchain_bp
from app.extensions import get_db, get_web3
from app.services.blockchain_service import BlockchainService
from app.middleware.auth_middleware import jwt_required, roles_required


@blockchain_bp.route("/health", methods=["GET"])
def blockchain_health():
    return jsonify({"status": "blockchain service ready"}), 200


@blockchain_bp.route("/status", methods=["GET"])
@jwt_required
@roles_required("admin")
def blockchain_status():
    """Get Ganache connection status (admin only)."""
    bc = BlockchainService(get_db(), get_web3())
    return jsonify({"blockchain": bc.get_status()}), 200


@blockchain_bp.route("/anchors/patient", methods=["GET"])
@jwt_required
@roles_required("patient")
def my_anchors():
    """Get all blockchain anchors for current patient."""
    bc = BlockchainService(get_db(), get_web3())
    anchors = bc.get_anchors_for_patient(g.current_user_id)
    return jsonify({"anchors": anchors, "count": len(anchors)}), 200
