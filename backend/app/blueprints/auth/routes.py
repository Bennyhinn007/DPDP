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


# ─────────────────────────────────────────────────────────────────────
# MFA (Google Authenticator)
# ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/mfa/setup", methods=["POST"])
@jwt_required
def mfa_setup():
    """
    Generate MFA secret and QR code for Google Authenticator.

    Returns provisioning URI and QR code (base64 PNG).
    """
    from app.services.mfa_service import MFAService
    from app.services.audit_service import AuditService

    svc = MFAService(get_db())
    result = svc.setup_mfa(g.current_user_id)

    # Audit
    audit = AuditService(get_db())
    audit.log_event(
        actor_id=g.current_user_id,
        actor_role=g.current_user_role,
        action_type="update",
        resource_type="mfa",
        resource_id=g.current_user_id,
        reason="MFA setup initiated",
        source_ip=request.remote_addr,
    )

    return jsonify(result), 200


@auth_bp.route("/mfa/verify", methods=["POST"])
@jwt_required
def mfa_verify():
    """
    Verify TOTP code and enable MFA.

    Body: { "code": "123456" }
    """
    from app.services.mfa_service import MFAService
    from app.services.audit_service import AuditService

    data = request.get_json()
    if not data or not data.get("code"):
        raise ValidationError("6-digit code required")

    svc = MFAService(get_db())
    result = svc.verify_and_enable(g.current_user_id, data["code"])

    # Audit
    audit = AuditService(get_db())
    audit.log_event(
        actor_id=g.current_user_id,
        actor_role=g.current_user_role,
        action_type="update",
        resource_type="mfa",
        resource_id=g.current_user_id,
        reason="MFA enabled successfully",
        severity="warning",
        source_ip=request.remote_addr,
    )

    return jsonify(result), 200


@auth_bp.route("/mfa/disable", methods=["POST"])
@jwt_required
def mfa_disable():
    """
    Disable MFA (requires valid TOTP code).

    Body: { "code": "123456" }
    """
    from app.services.mfa_service import MFAService
    from app.services.audit_service import AuditService

    data = request.get_json()
    if not data or not data.get("code"):
        raise ValidationError("6-digit code required to disable MFA")

    svc = MFAService(get_db())
    result = svc.disable_mfa(g.current_user_id, data["code"])

    # Audit
    audit = AuditService(get_db())
    audit.log_event(
        actor_id=g.current_user_id,
        actor_role=g.current_user_role,
        action_type="update",
        resource_type="mfa",
        resource_id=g.current_user_id,
        reason="MFA disabled",
        severity="critical",
        source_ip=request.remote_addr,
    )

    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────
# WEBAUTHN (Biometric Enrollment)
# ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/webauthn/register/begin", methods=["POST"])
@jwt_required
@roles_required("admin", "dpo")
def webauthn_register_begin():
    """
    Begin WebAuthn biometric registration (Admin/DPO only).

    Returns PublicKeyCredentialCreationOptions for navigator.credentials.create().
    """
    from app.services.webauthn_service import WebAuthnService
    from app.services.audit_service import AuditService

    auth_service = _get_auth_service()
    user = auth_service.get_user_by_id(g.current_user_id)
    if not user:
        return jsonify({"error": True, "message": "User not found"}), 404

    svc = WebAuthnService(get_db())
    options = svc.begin_registration(
        user_id=g.current_user_id,
        user_name=user["full_name"],
        user_email=user["email"],
    )

    return jsonify({"options": options}), 200


@auth_bp.route("/webauthn/register/complete", methods=["POST"])
@jwt_required
@roles_required("admin", "dpo")
def webauthn_register_complete():
    """
    Complete WebAuthn biometric registration.

    Body: { credential_id, public_key, attestation_object, client_data_json, device_name }
    """
    from app.services.webauthn_service import WebAuthnService
    from app.services.audit_service import AuditService

    data = request.get_json()
    if not data or not data.get("credential_id"):
        raise ValidationError("Credential data required")

    svc = WebAuthnService(get_db())
    result = svc.complete_registration(
        user_id=g.current_user_id,
        credential_id=data["credential_id"],
        public_key=data.get("public_key", ""),
        attestation_object=data.get("attestation_object", ""),
        client_data_json=data.get("client_data_json", ""),
        device_name=data.get("device_name", "Biometric Device"),
    )

    # Audit
    audit = AuditService(get_db())
    audit.log_event(
        actor_id=g.current_user_id,
        actor_role=g.current_user_role,
        action_type="create",
        resource_type="webauthn",
        resource_id=result.get("credential_id", ""),
        reason=f"WebAuthn biometric registered: {data.get('device_name', 'Device')}",
        severity="warning",
        source_ip=request.remote_addr,
    )

    return jsonify(result), 201


@auth_bp.route("/webauthn/credentials", methods=["GET"])
@jwt_required
def webauthn_list_credentials():
    """List registered WebAuthn credentials."""
    from app.services.webauthn_service import WebAuthnService

    svc = WebAuthnService(get_db())
    credentials = svc.list_credentials(g.current_user_id)
    has_biometric = svc.has_credentials(g.current_user_id)

    return jsonify({
        "credentials": credentials,
        "biometric_enabled": has_biometric,
        "count": len(credentials),
    }), 200


@auth_bp.route("/webauthn/credentials/<cred_id>", methods=["DELETE"])
@jwt_required
@roles_required("admin", "dpo")
def webauthn_remove_credential(cred_id):
    """Remove a registered WebAuthn credential."""
    from app.services.webauthn_service import WebAuthnService
    from app.services.audit_service import AuditService

    svc = WebAuthnService(get_db())
    removed = svc.remove_credential(g.current_user_id, cred_id)

    if not removed:
        return jsonify({"error": True, "message": "Credential not found"}), 404

    # Audit
    audit = AuditService(get_db())
    audit.log_event(
        actor_id=g.current_user_id,
        actor_role=g.current_user_role,
        action_type="delete",
        resource_type="webauthn",
        resource_id=cred_id,
        reason="WebAuthn biometric credential removed",
        severity="warning",
        source_ip=request.remote_addr,
    )

    return jsonify({"message": "Credential removed", "id": cred_id}), 200
