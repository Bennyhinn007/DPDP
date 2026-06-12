"""
Audit Middleware.

Provides a helper to log audit events from within route handlers.
Called explicitly by service methods after operations complete.
"""

from flask import request, g
from app.extensions import get_db
from app.services.audit_service import AuditService


def log_audit_event(
    action_type: str,
    resource_type: str,
    resource_id: str = None,
    patient_id: str = None,
    reason: str = None,
    details: dict = None,
    severity: str = "info",
):
    """
    Helper to log an audit event using the current request context.

    Call this from route handlers after an operation succeeds.
    Extracts actor info from flask.g (set by jwt_required).
    """
    actor_id = getattr(g, "current_user_id", "system")
    actor_role = getattr(g, "current_user_role", "system")

    svc = AuditService(get_db())
    return svc.log_event(
        actor_id=actor_id,
        actor_role=actor_role,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        patient_id=patient_id,
        reason=reason,
        details=details,
        severity=severity,
        source_ip=request.remote_addr if request else None,
        user_agent=request.headers.get("User-Agent") if request else None,
    )


def log_data_access(
    patient_id: str,
    accessor_name: str,
    access_type: str,
    data_categories: list,
    purpose: str,
    consent_id: str = None,
):
    """
    Helper to log a data access event for patient timeline.
    """
    accessor_id = getattr(g, "current_user_id", "system")
    accessor_role = getattr(g, "current_user_role", "system")

    svc = AuditService(get_db())
    return svc.log_data_access(
        patient_id=patient_id,
        accessor_id=accessor_id,
        accessor_role=accessor_role,
        accessor_name=accessor_name,
        access_type=access_type,
        data_categories=data_categories,
        purpose=purpose,
        consent_id=consent_id,
    )
