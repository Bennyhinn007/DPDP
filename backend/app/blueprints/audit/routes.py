"""
Audit Blueprint Routes.

Patient-facing timeline and DPO/Admin audit oversight APIs.
"""

from flask import request, jsonify, g

from app.blueprints.audit import audit_bp
from app.extensions import get_db
from app.services.audit_service import AuditService
from app.services.patient_service import PatientService
from app.middleware.auth_middleware import jwt_required, roles_required


def _get_audit_service():
    return AuditService(get_db())


def _get_patient_id(user_id: str) -> str:
    svc = PatientService(get_db())
    patient = svc.get_patient_by_user_id(user_id)
    return patient["_id"]


# ─────────────────────────────────────────────────────────────────────
# PATIENT TIMELINE
# ─────────────────────────────────────────────────────────────────────

@audit_bp.route("/timeline", methods=["GET"])
@jwt_required
@roles_required("patient")
def get_my_timeline():
    """
    Get audit timeline for the current patient.

    Query params:
        action_type: Filter by action type
        skip: Pagination offset
        limit: Max results (default 20)
    """
    # Use user_id directly — audit_logs stores user_id as patient_id
    user_id = g.current_user_id
    svc = _get_audit_service()

    events = svc.get_patient_timeline(
        patient_id=user_id,
        skip=request.args.get("skip", 0, type=int),
        limit=request.args.get("limit", 20, type=int),
        action_type=request.args.get("action_type"),
    )

    return jsonify({"timeline": events, "count": len(events)}), 200


@audit_bp.route("/access-history", methods=["GET"])
@jwt_required
@roles_required("patient")
def get_my_access_history():
    """
    Get data access history (who accessed patient's data).

    Query params:
        accessor_role: Filter by accessor role
        data_category: Filter by category
        skip: Pagination offset
        limit: Max results (default 20)
    """
    # Use user_id directly — data_access_logs stores user_id as patient_id
    user_id = g.current_user_id
    svc = _get_audit_service()

    history = svc.get_data_access_history(
        patient_id=user_id,
        skip=request.args.get("skip", 0, type=int),
        limit=request.args.get("limit", 20, type=int),
        accessor_role=request.args.get("accessor_role"),
        data_category=request.args.get("data_category"),
    )

    summary = svc.get_timeline_summary(user_id)

    return jsonify({
        "access_history": history,
        "count": len(history),
        "summary": summary,
    }), 200


# ─────────────────────────────────────────────────────────────────────
# DPO / ADMIN OVERSIGHT
# ─────────────────────────────────────────────────────────────────────

@audit_bp.route("/logs", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_all_logs():
    """
    Get all audit logs (admin/DPO only).

    Query params:
        action_type, severity, actor_id, resource_type, skip, limit
    """
    svc = _get_audit_service()

    logs = svc.get_all_logs(
        skip=request.args.get("skip", 0, type=int),
        limit=request.args.get("limit", 50, type=int),
        action_type=request.args.get("action_type"),
        severity=request.args.get("severity"),
        actor_id=request.args.get("actor_id"),
        resource_type=request.args.get("resource_type"),
    )

    return jsonify({"logs": logs, "count": len(logs)}), 200


@audit_bp.route("/logs/<log_id>", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_log_detail(log_id):
    """Get a single audit log entry (admin/DPO only)."""
    svc = _get_audit_service()
    log = svc.get_log_by_id(log_id)
    return jsonify({"log": log}), 200


@audit_bp.route("/stats", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_audit_stats():
    """Get aggregate audit statistics (admin/DPO only)."""
    svc = _get_audit_service()
    stats = svc.get_audit_stats()
    return jsonify({"stats": stats}), 200
