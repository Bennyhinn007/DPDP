"""
Integrity Verification Blueprint.

Provides endpoints for patients to verify their healthcare records
against blockchain-stored hashes.
"""

from flask import request, jsonify, g

from app.blueprints.integrity import integrity_bp
from app.extensions import get_db, get_web3
from app.services.blockchain_service import BlockchainService
from app.services.patient_service import PatientService
from app.middleware.auth_middleware import jwt_required, roles_required
from app.utils.errors import NotFoundError, AuthorizationError


def _get_bc_service():
    return BlockchainService(get_db(), get_web3())


@integrity_bp.route("/health", methods=["GET"])
def integrity_health():
    """Health check."""
    return jsonify({"status": "integrity service ready"}), 200


@integrity_bp.route("/record/<record_id>", methods=["GET"])
@jwt_required
@roles_required("patient", "admin")
def verify_record(record_id):
    """
    Verify a single healthcare record against its blockchain anchor.

    Returns:
        current_hash: SHA-256 of current record state
        blockchain_hash: Hash stored on-chain at creation/last update
        status: VERIFIED | INTEGRITY_VIOLATION | NO_ANCHOR
    """
    db = get_db()
    records = db["healthcare_records"]

    # Fetch raw record (encrypted state — hashes must match encrypted form)
    record = records.find_one({"_id": record_id})
    if not record:
        raise NotFoundError("Healthcare record not found")

    # Ownership check for patients
    if g.current_user_role == "patient":
        patients = db["patients"]
        patient = patients.find_one({"user_id": g.current_user_id})
        if not patient or record["patient_id"] != patient["_id"]:
            raise AuthorizationError("You can only verify your own records")

    bc = _get_bc_service()
    result = bc.verify_record("healthcare_records", record_id, record)

    return jsonify({"verification": result}), 200


@integrity_bp.route("/status", methods=["GET"])
@jwt_required
@roles_required("patient", "admin")
def blockchain_status():
    """Get blockchain connection status."""
    bc = _get_bc_service()
    status = bc.get_status()
    return jsonify({"blockchain": status}), 200


@integrity_bp.route("/anchors/<record_id>", methods=["GET"])
@jwt_required
@roles_required("patient", "admin")
def get_record_anchors(record_id):
    """Get all blockchain anchors for a specific record."""
    db = get_db()
    anchors = list(
        db["blockchain_anchors"].find({"resource_id": record_id}).sort("created_at", -1)
    )
    return jsonify({"anchors": anchors, "count": len(anchors)}), 200
