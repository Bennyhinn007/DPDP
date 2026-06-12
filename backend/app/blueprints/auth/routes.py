"""
Auth Blueprint Routes.

Handles user registration, login, token refresh, and protected test endpoint.
"""

import os
from flask import request, jsonify, g

from app.blueprints.auth import auth_bp
from app.extensions import get_db
from app.config import get_config
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import jwt_required, roles_required
from app.middleware.audit_middleware import log_audit_event
from app.utils.errors import ValidationError


def _get_auth_service():
    """Create AuthService with current config."""
    db = get_db()
    config = get_config(os.environ.get("FLASK_ENV", "development"))
    return AuthService(db, config)


@auth_bp.route("/health", methods=["GET"])
def auth_health():
    """Health check for auth service."""
    return jsonify({"status": "auth service ready"}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    Request Body:
        {
            "email": "user@example.com",
            "password": "securePassword123",
            "role": "patient",
            "full_name": "Rajesh Kumar"
        }

    Returns:
        201: User created successfully
        422: Validation error
    """
    data = request.get_json()
    if not data:
        raise ValidationError("Request body required")

    auth_service = _get_auth_service()
    user = auth_service.register(
        email=data.get("email", "").strip(),
        password=data.get("password", ""),
        role=data.get("role", "").strip(),
        full_name=data.get("full_name", "").strip(),
    )

    # Audit: registration event
    from app.services.audit_service import AuditService
    audit_svc = AuditService(get_db())
    audit_svc.log_event(
        actor_id=user["id"],
        actor_role=user["role"],
        action_type="create",
        resource_type="users",
        resource_id=user["id"],
        patient_id=user["id"] if user["role"] == "patient" else None,
        reason="User registration",
        details={"role": user["role"]},
        source_ip=request.remote_addr,
    )

    return jsonify({
        "message": "Registration successful",
        "user": user,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user and return JWT tokens.

    Request Body:
        {
            "email": "user@example.com",
            "password": "securePassword123"
        }

    Returns:
        200: Login successful with tokens
        401: Invalid credentials
    """
    data = request.get_json()
    if not data:
        raise ValidationError("Request body required")

    auth_service = _get_auth_service()
    result = auth_service.login(
        email=data.get("email", "").strip(),
        password=data.get("password", ""),
    )

    # Audit: login event
    from app.services.audit_service import AuditService
    audit_svc = AuditService(get_db())
    audit_svc.log_event(
        actor_id=result["user"]["id"],
        actor_role=result["user"]["role"],
        action_type="login",
        resource_type="auth",
        resource_id=result["user"]["id"],
        patient_id=result["user"]["id"] if result["user"]["role"] == "patient" else None,
        reason="User login",
        source_ip=request.remote_addr,
    )

    return jsonify(result), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user():
    """
    Get current authenticated user profile.

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: User profile
        401: Invalid/expired token
    """
    auth_service = _get_auth_service()
    user = auth_service.get_user_by_id(g.current_user_id)
    if not user:
        return jsonify({"error": True, "message": "User not found"}), 404

    return jsonify({"user": user}), 200


@auth_bp.route("/protected-test", methods=["GET"])
@jwt_required
def protected_test():
    """
    Test endpoint to verify JWT authentication works.

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Authentication confirmed with user context
    """
    return jsonify({
        "message": "JWT authentication successful",
        "user_id": g.current_user_id,
        "role": g.current_user_role,
    }), 200


@auth_bp.route("/admin-only", methods=["GET"])
@jwt_required
@roles_required("admin")
def admin_only():
    """
    Test endpoint to verify RBAC (admin-only access).

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Admin access confirmed
        403: Non-admin role rejected
    """
    return jsonify({
        "message": "Admin access granted",
        "user_id": g.current_user_id,
        "role": g.current_user_role,
    }), 200


@auth_bp.route("/patient-only", methods=["GET"])
@jwt_required
@roles_required("patient")
def patient_only():
    """
    Test endpoint to verify RBAC (patient-only access).

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Patient access confirmed
        403: Non-patient role rejected
    """
    return jsonify({
        "message": "Patient access granted",
        "user_id": g.current_user_id,
        "role": g.current_user_role,
    }), 200
