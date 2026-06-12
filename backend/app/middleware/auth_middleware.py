"""
Authentication Middleware.

Provides decorators for JWT verification and role-based access control.
"""

from functools import wraps
from flask import request, g

from app.extensions import get_db
from app.config import get_config
from app.services.auth_service import AuthService
from app.utils.errors import AuthenticationError, AuthorizationError


def get_auth_service():
    """Get AuthService instance using current app config."""
    import os
    db = get_db()
    config = get_config(os.environ.get("FLASK_ENV", "development"))
    return AuthService(db, config)


def jwt_required(f):
    """
    Decorator: Requires valid JWT access token.

    Extracts token from Authorization header, verifies it,
    and stores user info in flask.g for downstream use.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            raise AuthenticationError("Authorization header required")

        auth_service = get_auth_service()
        payload = auth_service.verify_token(token)

        # Verify token type
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")

        # Store user context in flask.g
        g.current_user_id = payload["sub"]
        g.current_user_role = payload["role"]
        g.token_payload = payload

        return f(*args, **kwargs)
    return decorated


def roles_required(*allowed_roles):
    """
    Decorator: Requires specific role(s).

    Must be used after @jwt_required.

    Usage:
        @jwt_required
        @roles_required("admin", "dpo")
        def admin_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_role = getattr(g, "current_user_role", None)
            if user_role not in allowed_roles:
                raise AuthorizationError(
                    f"Access denied. Required roles: {list(allowed_roles)}"
                )
            return f(*args, **kwargs)
        return decorated
    return decorator


def _extract_token() -> str:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return ""
