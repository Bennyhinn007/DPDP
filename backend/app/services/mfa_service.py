"""
MFA Service — TOTP (Google Authenticator).

RFC6238-compliant Time-Based One-Time Password.
Compatible with Google Authenticator, Authy, Microsoft Authenticator.
"""

import pyotp
import base64
import io
from typing import Optional

from app.utils.helpers import generate_uuid, utc_now
from app.utils.errors import ValidationError, AuthenticationError


class MFAService:
    """Manages TOTP-based Multi-Factor Authentication."""

    def __init__(self, db):
        self.db = db
        self.users = db["users"]

    def setup_mfa(self, user_id: str) -> dict:
        """
        Generate MFA secret and provisioning URI.

        Returns:
            Dict with secret, provisioning_uri, and qr_code_base64
        """
        user = self.users.find_one({"_id": user_id})
        if not user:
            raise ValidationError("User not found")

        if user.get("mfa_enabled"):
            raise ValidationError("MFA is already enabled for this account")

        # Generate TOTP secret
        secret = pyotp.random_base32()

        # Build provisioning URI
        email = user.get("email_encrypted", user.get("full_name", "user"))
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name="DPDP Healthcare Platform"
        )

        # Generate QR code as base64
        qr_base64 = self._generate_qr_base64(provisioning_uri)

        # Store secret temporarily (not enabled until verified)
        self.users.update_one(
            {"_id": user_id},
            {"$set": {"mfa_secret_pending": secret, "updated_at": utc_now()}}
        )

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_base64": qr_base64,
            "instructions": "Scan this QR code with Google Authenticator, then verify with a 6-digit code.",
        }

    def verify_and_enable(self, user_id: str, code: str) -> dict:
        """
        Verify TOTP code and enable MFA.

        Args:
            user_id: User UUID
            code: 6-digit TOTP code from authenticator app

        Returns:
            Success confirmation
        """
        user = self.users.find_one({"_id": user_id})
        if not user:
            raise ValidationError("User not found")

        pending_secret = user.get("mfa_secret_pending")
        if not pending_secret:
            raise ValidationError("No MFA setup in progress. Call /mfa/setup first.")

        # Verify the code
        totp = pyotp.TOTP(pending_secret)
        if not totp.verify(code, valid_window=1):
            raise AuthenticationError("Invalid verification code. Please try again.")

        # Enable MFA
        self.users.update_one(
            {"_id": user_id},
            {"$set": {
                "mfa_enabled": True,
                "mfa_secret": pending_secret,
                "mfa_enabled_at": utc_now(),
                "updated_at": utc_now(),
            }, "$unset": {"mfa_secret_pending": ""}}
        )

        return {"message": "MFA enabled successfully", "mfa_enabled": True}

    def verify_code(self, user_id: str, code: str) -> bool:
        """
        Verify TOTP code during login.

        Returns True if code is valid, raises AuthenticationError otherwise.
        """
        user = self.users.find_one({"_id": user_id})
        if not user or not user.get("mfa_secret"):
            raise AuthenticationError("MFA not configured")

        totp = pyotp.TOTP(user["mfa_secret"])
        if not totp.verify(code, valid_window=1):
            raise AuthenticationError("Invalid MFA code")

        return True

    def disable_mfa(self, user_id: str, code: str) -> dict:
        """
        Disable MFA (requires valid code for security).
        """
        user = self.users.find_one({"_id": user_id})
        if not user:
            raise ValidationError("User not found")

        if not user.get("mfa_enabled"):
            raise ValidationError("MFA is not enabled")

        # Verify code before disabling
        totp = pyotp.TOTP(user["mfa_secret"])
        if not totp.verify(code, valid_window=1):
            raise AuthenticationError("Invalid MFA code. Cannot disable.")

        self.users.update_one(
            {"_id": user_id},
            {"$set": {
                "mfa_enabled": False,
                "mfa_secret": None,
                "updated_at": utc_now(),
            }}
        )

        return {"message": "MFA disabled successfully", "mfa_enabled": False}

    @staticmethod
    def _generate_qr_base64(data: str) -> str:
        """Generate QR code as base64 PNG string."""
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except ImportError:
            # qrcode library not installed — return URI only
            return ""
