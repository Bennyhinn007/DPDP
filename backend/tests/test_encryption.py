"""
Tests for AES-256 Encryption (Day 6).

Tests prove:
1. MongoDB stores ciphertext (not plaintext)
2. API returns plaintext (correctly decrypted)
3. Decryption failure handled safely
4. Encryption service field/document operations work
"""

import pytest
from app import create_app
from app.extensions import get_db
from app.services.encryption_service import EncryptionService, get_encryption_service


@pytest.fixture
def app():
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db = get_db()
        for col in ["users", "patients", "healthcare_records",
                    "consents", "consent_receipts", "audit_logs"]:
            db[col].delete_many({})
    yield
    with app.app_context():
        db = get_db()
        for col in ["users", "patients", "healthcare_records",
                    "consents", "consent_receipts", "audit_logs"]:
            db[col].delete_many({})


def register_and_login(client, email="enc_test@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "TestPass123",
        "role": "patient", "full_name": "Encryption Test",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "TestPass123",
    })
    return resp.get_json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────
# ENCRYPTION SERVICE UNIT TESTS
# ─────────────────────────────────────────────────────────────────────

class TestEncryptionService:
    """Unit tests for EncryptionService."""

    def test_encrypt_decrypt_string(self):
        enc = EncryptionService()
        original = "Rajesh Kumar"
        encrypted = enc.encrypt_field(original)
        assert encrypted != original
        assert enc.is_encrypted(encrypted)
        decrypted = enc.decrypt_field(encrypted)
        assert decrypted == original

    def test_encrypt_decrypt_list(self):
        enc = EncryptionService()
        original = ["Penicillin", "Aspirin"]
        encrypted = enc.encrypt_field(original)
        assert isinstance(encrypted, str)
        assert enc.is_encrypted(encrypted)
        decrypted = enc.decrypt_field(encrypted)
        assert decrypted == original

    def test_encrypt_decrypt_dict(self):
        enc = EncryptionService()
        original = {"street": "21 Greams Lane", "city": "Chennai"}
        encrypted = enc.encrypt_field(original)
        decrypted = enc.decrypt_field(encrypted)
        assert decrypted == original

    def test_encrypt_none_returns_none(self):
        enc = EncryptionService()
        assert enc.encrypt_field(None) is None
        assert enc.decrypt_field(None) is None

    def test_decrypt_invalid_token_returns_failure_marker(self):
        enc = EncryptionService()
        # Non-Fernet strings pass through as plaintext (legacy data)
        result = enc.decrypt_field("not-valid-fernet-ciphertext")
        assert result == "not-valid-fernet-ciphertext"

    def test_decrypt_corrupted_ciphertext(self):
        enc = EncryptionService()
        # Valid-looking but corrupted Fernet token
        corrupted = "gAAAAABkZmFrZS1jaXBoZXJ0ZXh0LXRoYXQtaXMtY29ycnVwdGVkAAAA"
        result = enc.decrypt_field(corrupted)
        assert result == "[DECRYPTION_FAILED]"

    def test_encrypt_document_encrypts_sensitive_fields_only(self):
        enc = EncryptionService()
        doc = {
            "_id": "test-123",
            "patient_id": "patient-456",
            "full_name": "Rajesh Kumar",
            "phone_number": "+91-9876543210",
            "status": "active",
            "version": 1,
            "created_at": "2025-01-01",
        }
        encrypted = enc.encrypt_document(doc)

        # Non-sensitive fields unchanged
        assert encrypted["_id"] == "test-123"
        assert encrypted["patient_id"] == "patient-456"
        assert encrypted["status"] == "active"
        assert encrypted["version"] == 1
        assert encrypted["created_at"] == "2025-01-01"

        # Sensitive fields encrypted
        assert encrypted["full_name"] != "Rajesh Kumar"
        assert enc.is_encrypted(encrypted["full_name"])
        assert encrypted["phone_number"] != "+91-9876543210"
        assert enc.is_encrypted(encrypted["phone_number"])

    def test_decrypt_document_restores_plaintext(self):
        enc = EncryptionService()
        doc = {
            "_id": "test-123",
            "full_name": "Rajesh Kumar",
            "phone_number": "+91-9876543210",
            "status": "active",
        }
        encrypted = enc.encrypt_document(doc)
        decrypted = enc.decrypt_document(encrypted)

        assert decrypted["full_name"] == "Rajesh Kumar"
        assert decrypted["phone_number"] == "+91-9876543210"
        assert decrypted["status"] == "active"
        assert decrypted["_id"] == "test-123"

    def test_different_encryptions_produce_different_ciphertext(self):
        enc = EncryptionService()
        ct1 = enc.encrypt_field("same text")
        ct2 = enc.encrypt_field("same text")
        # Fernet includes timestamp so same plaintext → different ciphertext
        assert ct1 != ct2

    def test_generate_key(self):
        key = EncryptionService.generate_key()
        assert len(key) == 44  # Base64-encoded 32 bytes


# ─────────────────────────────────────────────────────────────────────
# INTEGRATION: MONGODB STORES CIPHERTEXT
# ─────────────────────────────────────────────────────────────────────

class TestMongoStoresCiphertext:
    """Prove that MongoDB stores encrypted data, not plaintext."""

    def test_patient_profile_stored_encrypted(self, client, app):
        token = register_and_login(client)

        # Update profile with sensitive data
        client.put("/api/v1/patients/me", json={
            "phone_number": "+91-9876543210",
            "blood_group": "O+",
            "allergies": ["Penicillin", "Dust"],
        }, headers=auth(token))

        # Read directly from MongoDB (bypassing decryption)
        with app.app_context():
            db = get_db()
            enc = get_encryption_service()
            raw = db["patients"].find_one({"user_id": {"$exists": True}})

            # Sensitive fields are ciphertext in DB
            assert raw["phone_number"] != "+91-9876543210"
            assert enc.is_encrypted(raw["phone_number"])
            assert raw["blood_group"] != "O+"
            assert enc.is_encrypted(raw["blood_group"])
            # allergies stored as encrypted JSON array
            assert raw["allergies"] != ["Penicillin", "Dust"]
            assert enc.is_encrypted(raw["allergies"])

            # Non-sensitive fields remain plaintext
            assert raw["version"] == 2
            assert raw["redacted"] is False

    def test_healthcare_record_stored_encrypted(self, client, app):
        token = register_and_login(client)

        # Create a healthcare record
        client.post("/api/v1/patients/me/records", json={
            "record_type": "consultation",
            "title": "Cardiology Follow-up",
            "description": "Patient presents with improved symptoms after medication.",
            "diagnosis_codes": ["I25.1"],
            "symptoms": ["mild_discomfort"],
            "treatment_notes": "Continue Aspirin 75mg daily.",
        }, headers=auth(token))

        # Read raw from MongoDB
        with app.app_context():
            db = get_db()
            enc = get_encryption_service()
            raw = db["healthcare_records"].find_one()

            # Encrypted fields
            assert raw["title"] != "Cardiology Follow-up"
            assert enc.is_encrypted(raw["title"])
            assert raw["description"] != "Patient presents with improved symptoms after medication."
            assert enc.is_encrypted(raw["description"])
            assert enc.is_encrypted(raw["diagnosis_codes"])
            assert enc.is_encrypted(raw["symptoms"])
            assert enc.is_encrypted(raw["treatment_notes"])

            # Non-sensitive remain plaintext
            assert raw["record_type"] == "consultation"
            assert raw["version"] == 1
            assert raw["status"] == "active"


# ─────────────────────────────────────────────────────────────────────
# INTEGRATION: API RETURNS PLAINTEXT
# ─────────────────────────────────────────────────────────────────────

class TestAPIReturnsPlaintext:
    """Prove that API responses contain decrypted plaintext."""

    def test_get_patient_returns_plaintext(self, client):
        token = register_and_login(client)

        # Update with sensitive data
        client.put("/api/v1/patients/me", json={
            "phone_number": "+91-5555555555",
            "blood_group": "A+",
            "allergies": ["Latex"],
        }, headers=auth(token))

        # API returns plaintext
        resp = client.get("/api/v1/patients/me", headers=auth(token))
        assert resp.status_code == 200
        data = resp.get_json()["patient"]
        assert data["phone_number"] == "+91-5555555555"
        assert data["blood_group"] == "A+"
        assert data["allergies"] == ["Latex"]

    def test_get_healthcare_record_returns_plaintext(self, client):
        token = register_and_login(client)

        resp = client.post("/api/v1/patients/me/records", json={
            "record_type": "diagnosis",
            "title": "Hypertension Diagnosis",
            "description": "Patient diagnosed with Stage 1 hypertension based on BP readings.",
            "diagnosis_codes": ["I10"],
            "symptoms": ["headache", "dizziness"],
            "treatment_notes": "Start Amlodipine 5mg once daily.",
        }, headers=auth(token))
        record_id = resp.get_json()["record"]["_id"]

        # Get it back — should be plaintext
        resp = client.get(f"/api/v1/patients/me/records/{record_id}", headers=auth(token))
        assert resp.status_code == 200
        rec = resp.get_json()["record"]
        assert rec["title"] == "Hypertension Diagnosis"
        assert rec["description"] == "Patient diagnosed with Stage 1 hypertension based on BP readings."
        assert rec["diagnosis_codes"] == ["I10"]
        assert rec["symptoms"] == ["headache", "dizziness"]
        assert rec["treatment_notes"] == "Start Amlodipine 5mg once daily."

    def test_list_records_returns_plaintext(self, client):
        token = register_and_login(client)

        client.post("/api/v1/patients/me/records", json={
            "record_type": "consultation",
            "title": "General Checkup",
            "description": "Routine annual health examination completed.",
        }, headers=auth(token))

        resp = client.get("/api/v1/patients/me/records", headers=auth(token))
        assert resp.status_code == 200
        records = resp.get_json()["records"]
        assert len(records) == 1
        assert records[0]["title"] == "General Checkup"


# ─────────────────────────────────────────────────────────────────────
# DECRYPTION FAILURE HANDLING
# ─────────────────────────────────────────────────────────────────────

class TestDecryptionFailure:
    """Test graceful handling of decryption failures."""

    def test_corrupted_field_returns_failure_marker(self, app):
        with app.app_context():
            db = get_db()
            enc = get_encryption_service()

            # Insert a document with corrupted ciphertext
            db["patients"].insert_one({
                "_id": "corrupted-patient",
                "user_id": "corrupted-user",
                "full_name": "gAAAAABkZmFrZS1jaXBoZXJ0ZXh0AAAAAAAAAA",
                "phone_number": None,
                "version": 1,
                "status": "active",
                "redacted": False,
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
                "created_by": "x",
                "updated_by": "x",
            })

            raw = db["patients"].find_one({"_id": "corrupted-patient"})
            decrypted = enc.decrypt_document(raw)

            # Corrupted field gets failure marker, doesn't crash
            assert decrypted["full_name"] == "[DECRYPTION_FAILED]"
            # Non-sensitive fields unaffected
            assert decrypted["_id"] == "corrupted-patient"
            assert decrypted["version"] == 1
