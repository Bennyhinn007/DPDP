"""
Compliance Blueprint Routes.

DPDP Compliance Dashboard — admin-only access.
Provides aggregated metrics, rights request tracking, and compliance scoring.
"""

from flask import request, jsonify

from app.blueprints.compliance import compliance_bp
from app.extensions import get_db
from app.services.compliance_service import ComplianceService
from app.middleware.auth_middleware import jwt_required, roles_required


def _get_compliance_service():
    return ComplianceService(get_db())


@compliance_bp.route("/dashboard", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_dashboard():
    """
    Get full compliance dashboard.

    Returns aggregated data from all collections for DPO/Admin overview.
    """
    svc = _get_compliance_service()
    dashboard = svc.get_dashboard()
    return jsonify({"dashboard": dashboard}), 200


@compliance_bp.route("/stats", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_stats():
    """Get concise compliance statistics."""
    svc = _get_compliance_service()
    stats = svc.get_stats()
    return jsonify({"stats": stats}), 200


@compliance_bp.route("/rights-requests", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_rights_requests():
    """
    Get DPDP rights requests (corrections + erasures).

    Query params:
        skip: Pagination offset
        limit: Max results (default 20)
    """
    svc = _get_compliance_service()
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 20, type=int)
    data = svc.get_rights_requests(skip=skip, limit=limit)
    return jsonify({"rights_requests": data}), 200


@compliance_bp.route("/compliance-score", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_compliance_score():
    """
    Get DPDP compliance score (0-100).

    Evaluates encryption, consent, audit, blockchain, and rights coverage.
    """
    svc = _get_compliance_service()
    score = svc.get_compliance_score()
    return jsonify({"compliance_score": score}), 200


# ─────────────────────────────────────────────────────────────────────
# IDENTITY GOVERNANCE
# ─────────────────────────────────────────────────────────────────────

@compliance_bp.route("/governance", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_governance_data():
    """
    Get Identity & Access Governance data.

    Returns user directory, lifecycle metrics, access security,
    and healthcare relationships for the admin governance center.
    """
    from app.services.admin_service import AdminService
    svc = AdminService(get_db())
    data = svc.get_governance_data()
    return jsonify({"governance": data}), 200


@compliance_bp.route("/unlock-user/<user_id>", methods=["POST"])
@jwt_required
@roles_required("admin")
def unlock_user(user_id):
    """
    Admin: Manually unlock a locked user account.

    Resets failed_login_attempts and removes locked_until.
    Creates audit entry for ACCOUNT_UNLOCKED.
    """
    from app.services.audit_service import AuditService
    from app.utils.helpers import utc_now
    from flask import g

    db = get_db()
    user = db["users"].find_one({"_id": user_id})
    if not user:
        return jsonify({"error": True, "message": "User not found"}), 404

    db["users"].update_one(
        {"_id": user_id},
        {"$set": {
            "failed_login_attempts": 0,
            "locked_until": None,
            "updated_at": utc_now(),
        }}
    )

    # Audit
    audit = AuditService(db)
    audit.log_event(
        actor_id=g.current_user_id,
        actor_role="admin",
        action_type="update",
        resource_type="users",
        resource_id=user_id,
        reason=f"Account manually unlocked by admin",
        severity="warning",
    )

    return jsonify({"message": "Account unlocked successfully", "user_id": user_id}), 200
