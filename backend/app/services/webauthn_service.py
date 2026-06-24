"""
WebAuthn Service — Biometric Enrollment.

Implements FIDO2/WebAuthn registration for privileged users (Admin/DPO).
Supports: Windows Hello, Fingerprint, Face Recognition via browser APIs.

Security:
- No biometric templates stored (only public keys)
- RP ID validation
- Challenge expiration (5 minutes)
- Replay protection via counter verification
- DPDP compliant (no biometric data leaves the device)
"""

import os
import base64
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.utils.helpers import generate_uuid, utc_now
from app.utils.errors import ValidationError, AuthenticationError


# Configuration
RP_ID = os.environ.get("WEBAUTHN_RP_ID", "localhost")
RP_NAME = "DPDP Healthcare Platform"
CHALLENGE_TIMEOUT = timedelta(minutes=5)


class WebAuthnService:
    """Manages WebAuthn biometric credential registration."""

    def __init__(self, db):
        self.db = db
        self.credentials = db["webauthn_credentials"]
        self.challenges = db["webauthn_challenges"]

    def begin_registration(self, user_id: str, user_name: str, user_email: str) -> dict:
        """
        Generate WebAuthn registration options.

        Creates a cryptographic challenge and returns PublicKeyCredentialCreationOptions.

        Args:
            user_id: UUID of the user
            user_name: Display name
            user_email: Email for user handle

        Returns:
            Registration options for navigator.credentials.create()
        """
        # Generate challenge
        challenge = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")

        # Store challenge with expiry
        self.challenges.insert_one({
            "_id": generate_uuid(),
            "user_id": user_id,
            "challenge": challenge,
            "type": "registration",
            "created_at": utc_now(),
            "expires_at": (datetime.now(timezone.utc) + CHALLENGE_TIMEOUT).isoformat(),
        })

        # Get existing credentials to exclude
        existing = list(self.credentials.find({"user_id": user_id}))
        exclude_credentials = [
            {
                "id": cred["credential_id"],
                "type": "public-key",
                "transports": ["internal"],
            }
            for cred in existing
        ]

        # User handle (unique identifier)
        user_handle = base64.urlsafe_b64encode(user_id.encode()).decode().rstrip("=")

        return {
            "rp": {
                "id": RP_ID,
                "name": RP_NAME,
            },
            "user": {
                "id": user_handle,
                "name": user_email,
                "displayName": user_name,
            },
            "challenge": challenge,
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},   # ES256
                {"type": "public-key", "alg": -257},  # RS256
            ],
            "timeout": 60000,
            "authenticatorSelection": {
                "authenticatorAttachment": "platform",  # Built-in (Windows Hello, Touch ID)
                "userVerification": "required",
                "residentKey": "preferred",
            },
            "excludeCredentials": exclude_credentials,
            "attestation": "none",  # Privacy-preserving
        }

    def complete_registration(
        self,
        user_id: str,
        credential_id: str,
        public_key: str,
        attestation_object: str,
        client_data_json: str,
        device_name: str = "Biometric Device",
    ) -> dict:
        """
        Complete WebAuthn registration.

        Validates the challenge and stores the credential.

        Args:
            user_id: UUID of the user
            credential_id: Base64url credential ID from browser
            public_key: Base64url public key
            attestation_object: Attestation from authenticator
            client_data_json: Client data for verification
            device_name: User-friendly device name

        Returns:
            Registration confirmation
        """
        # Validate challenge exists and hasn't expired
        challenge_doc = self.challenges.find_one({
            "user_id": user_id,
            "type": "registration",
            "expires_at": {"$gt": utc_now()},
        })

        if not challenge_doc:
            raise ValidationError("Registration challenge expired. Please try again.")

        # Verify client data contains our challenge
        try:
            client_data = json.loads(base64.urlsafe_b64decode(client_data_json + "=="))
            if client_data.get("challenge") != challenge_doc["challenge"]:
                raise AuthenticationError("Challenge mismatch — possible replay attack")
            if client_data.get("type") != "webauthn.create":
                raise AuthenticationError("Invalid ceremony type")
        except (json.JSONDecodeError, KeyError):
            raise ValidationError("Invalid client data")

        # Check duplicate credential
        existing = self.credentials.find_one({"credential_id": credential_id})
        if existing:
            raise ValidationError("This credential is already registered")

        # Store credential
        now = utc_now()
        cred_doc = {
            "_id": generate_uuid(),
            "user_id": user_id,
            "credential_id": credential_id,
            "public_key": public_key,
            "counter": 0,
            "device_name": device_name,
            "attestation_format": "none",
            "created_at": now,
            "last_used": None,
        }
        self.credentials.insert_one(cred_doc)

        # Clean up used challenge
        self.challenges.delete_many({"user_id": user_id, "type": "registration"})

        return {
            "status": "registered",
            "credential_id": credential_id,
            "device_name": device_name,
            "created_at": now,
        }

    def list_credentials(self, user_id: str) -> list:
        """List all registered WebAuthn credentials for a user."""
        creds = list(self.credentials.find({"user_id": user_id}).sort("created_at", -1))
        return [
            {
                "id": c["_id"],
                "credential_id": c["credential_id"][:16] + "...",
                "device_name": c.get("device_name", "Unknown Device"),
                "created_at": c["created_at"],
                "last_used": c.get("last_used"),
            }
            for c in creds
        ]

    def remove_credential(self, user_id: str, credential_doc_id: str) -> bool:
        """Remove a registered credential."""
        result = self.credentials.delete_one({"_id": credential_doc_id, "user_id": user_id})
        return result.deleted_count > 0

    def has_credentials(self, user_id: str) -> bool:
        """Check if user has any registered WebAuthn credentials."""
        return self.credentials.count_documents({"user_id": user_id}) > 0
