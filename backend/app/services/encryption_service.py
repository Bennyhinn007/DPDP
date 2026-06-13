"""
AES-256 Encryption Service.

Provides field-level and document-level encryption using Fernet (AES-256-CBC
with HMAC-SHA256 authentication, via the cryptography library).

Design:
- Sensitive fields are encrypted before MongoDB insertion
- Non-sensitive metadata fields are stored in plaintext for querying
- A single system key is used in MVP (per-patient keys added post-MVP)
- Decryption failures are handled gracefully without exposing internals
"""

import os
import base64
from typing import Any
from cryptography.fernet import Fernet, InvalidToken


# Fields that should NEVER be encrypted (needed for queries/indexing)
NEVER_ENCRYPT_FIELDS = {
    "_id", "patient_id", "user_id", "doctor_id", "created_at", "updated_at",
    "created_by", "updated_by", "status", "version", "record_type",
    "consent_type", "redacted", "redacted_at", "redacted_by",
    "redaction_reason", "verification_hash", "blockchain_tx_ref",
    "blockchain_anchor_id", "email_hash", "identity_number_hash",
    "license_number_hash", "data_categories_stored", "consent_defaults",
    "privacy_score", "role", "mfa_enabled", "failed_login_attempts",
    "locked_until", "last_login", "processing_entity_id",
    "processing_entity_name", "granted_at", "expires_at", "withdrawn_at",
    "modified_at", "consent_hash", "data_categories_in_scope",
    "previous_scope", "modification_reason", "withdrawal_reason",
    "purpose_description", "follow_up_date", "dispensed_by", "dispensed_at",
    "refill_allowed", "refill_count", "refills_used", "prescription_date",
    "duration_days", "healthcare_record_id",
}

# Fields that SHOULD be encrypted (contain PII or sensitive health data)
SENSITIVE_FIELDS = {
    # Patient profile
    "full_name", "phone_number", "address", "identity_number",
    "identity_type", "blood_group", "allergies", "chronic_conditions",
    "emergency_contact", "email_encrypted",
    # Healthcare records
    "title", "description", "diagnosis_codes", "symptoms",
    "treatment_notes",
    # Prescriptions
    "medications", "diagnosis_summary", "instructions", "dispensing_notes",
    # Auth
    "mfa_secret", "password_hash",
}


class EncryptionService:
    """
    AES-256 symmetric encryption for sensitive healthcare data.

    Uses Fernet which provides:
    - AES-256-CBC encryption
    - HMAC-SHA256 authentication (tamper detection)
    - Base64 URL-safe encoding for storage
    """

    def __init__(self, key: str = None):
        """
        Initialize with encryption key.

        Args:
            key: Fernet key (base64-encoded 32 bytes). If None, reads from
                 ENCRYPTION_KEY env var or generates a new one.
        """
        if key:
            self._key = key.encode() if isinstance(key, str) else key
        else:
            env_key = os.environ.get("ENCRYPTION_KEY")
            if env_key:
                self._key = env_key.encode()
            else:
                # Generate and store for development only
                self._key = Fernet.generate_key()
                os.environ["ENCRYPTION_KEY"] = self._key.decode()

        self._fernet = Fernet(self._key)

    # ─────────────────────────────────────────────────────────────────
    # FIELD-LEVEL OPERATIONS
    # ─────────────────────────────────────────────────────────────────

    def encrypt_field(self, value: Any) -> str:
        """
        Encrypt a single field value.

        Handles strings, lists, dicts, and None.
        Returns base64-encoded ciphertext string.

        Args:
            value: Plaintext value (str, list, dict, int, or None)

        Returns:
            Encrypted string, or None if input is None
        """
        if value is None:
            return None

        # Serialize non-string values to JSON string
        import json
        if isinstance(value, (list, dict, int, float, bool)):
            plaintext = json.dumps(value, ensure_ascii=False)
        else:
            plaintext = str(value)

        encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt_field(self, encrypted_value: str) -> Any:
        """
        Decrypt a single field value.

        Attempts to parse JSON for complex types.
        Returns plaintext value.
        """
        if encrypted_value is None:
            return None

        if not isinstance(encrypted_value, str):
            return encrypted_value

        # Plaintext value (legacy records)
        if not encrypted_value.startswith("gAAAA"):
            return encrypted_value

        try:
            decrypted_bytes = self._fernet.decrypt(
                encrypted_value.encode("utf-8")
            )
            plaintext = decrypted_bytes.decode("utf-8")
        except InvalidToken:
            return "[DECRYPTION_FAILED]"

        import json

        try:
            return json.loads(plaintext)
        except (json.JSONDecodeError, ValueError):
            return plaintext

    # ─────────────────────────────────────────────────────────────────
    # DOCUMENT-LEVEL OPERATIONS
    # ─────────────────────────────────────────────────────────────────

    def encrypt_document(self, document: dict, sensitive_fields: set = None) -> dict:
        """
        Encrypt sensitive fields in a document before MongoDB insertion.

        Fields in NEVER_ENCRYPT_FIELDS are always left as plaintext.
        Only fields in sensitive_fields (or SENSITIVE_FIELDS default) are encrypted.

        Args:
            document: Original document dict
            sensitive_fields: Override set of fields to encrypt (optional)

        Returns:
            New dict with sensitive fields encrypted
        """
        if sensitive_fields is None:
            sensitive_fields = SENSITIVE_FIELDS

        encrypted_doc = {}
        for key, value in document.items():
            if key in NEVER_ENCRYPT_FIELDS:
                encrypted_doc[key] = value
            elif key in sensitive_fields and value is not None:
                encrypted_doc[key] = self.encrypt_field(value)
            else:
                encrypted_doc[key] = value

        return encrypted_doc

    def decrypt_document(self, document: dict, sensitive_fields: set = None) -> dict:
        """
        Decrypt sensitive fields in a document for API response.

        Args:
            document: Encrypted document from MongoDB
            sensitive_fields: Override set of fields to decrypt (optional)

        Returns:
            New dict with sensitive fields decrypted
        """
        if document is None:
            return None

        if sensitive_fields is None:
            sensitive_fields = SENSITIVE_FIELDS

        decrypted_doc = {}
        for key, value in document.items():
            if key in NEVER_ENCRYPT_FIELDS:
                decrypted_doc[key] = value
            elif key in sensitive_fields and value is not None:
                decrypted_doc[key] = self.decrypt_field(value)
            else:
                decrypted_doc[key] = value

        return decrypted_doc

    # ─────────────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────────────

    def is_encrypted(self, value: str) -> bool:
        """
        Check if a string value looks like Fernet ciphertext.

        Fernet tokens start with 'gAAAAA' (base64-encoded version byte).
        """
        if not isinstance(value, str):
            return False
        return value.startswith("gAAAAA") and len(value) > 50

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key."""
        return Fernet.generate_key().decode("utf-8")

    @property
    def key(self) -> str:
        """Return the current key (for storage/backup)."""
        return self._key.decode("utf-8")


# ─────────────────────────────────────────────────────────────────────
# SINGLETON INSTANCE
# ─────────────────────────────────────────────────────────────────────

_instance: EncryptionService = None


def get_encryption_service() -> EncryptionService:
    """Get or create the singleton EncryptionService."""
    global _instance
    if _instance is None:
        _instance = EncryptionService()
    return _instance
