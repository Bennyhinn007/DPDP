"""
Tests for Consent Management (Day 4).

Tests cover:
- Grant consent (all 6 types, validation, duplicates)
- List consents (all, by status, by type)
- Get single consent (ownership)
- Modify consent scope
- Withdraw consent (immediate revocation)
- Consent receipts
- Expiry tracking
"""

import pytest
from app import create_app
from app.extensions import get_db


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
        db["users"].delete_many({})
        db["patients"].delete_many({})
        db["consents"].delete_many({})
        db["consent_receipts"].delete_many({})
    yield
    with app.app_context():
        db = get_db()
        db["users"].delete_many({})
        db["patients"].delete_many({})
        db["consents"].delete_many({})
        db["consent_receipts"].delete_many({})


def register_and_login(client, email="patient@test.com", role="patient"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "TestPass123",
        "role": role, "full_name": "Test Patient",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": "TestPass123",
    })
    return resp.get_json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def grant(client, token, consent_type="healthcare_treatment", entity="Apollo Healthcare"):
    return client.post("/api/v1/consents/grant", json={
        "consent_type": consent_type,
        "processing_entity_name": entity,
        "expiry_days": 365,
    }, headers=auth(token))


class TestGrantConsent:
    """Test consent grant operations."""

    def test_grant_healthcare_treatment(self, client):
        token = register_and_login(client)
        resp = grant(client, token, "healthcare_treatment")
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["consent"]["consent_type"] == "healthcare_treatment"
        assert data["consent"]["status"] == "active"
        assert data["consent"]["processing_entity_name"] == "Apollo Healthcare"
        assert "medical_history" in data["consent"]["data_categories_in_scope"]
        assert data["receipt"]["action_type"] == "grant"

    def test_grant_pharmacy_access(self, client):
        token = register_and_login(client)
        resp = grant(client, token, "pharmacy_access", "Central Pharmacy")
        assert resp.status_code == 201
        scope = resp.get_json()["consent"]["data_categories_in_scope"]
        assert "prescriptions" in scope
        assert "allergies" in scope
        assert "medical_history" not in scope  # Purpose limitation

    def test_grant_all_six_types(self, client):
        token = register_and_login(client)
        types = [
            "healthcare_treatment", "pharmacy_access", "research_access",
            "insurance_access", "analytics_access", "marketing_access",
        ]
        for ct in types:
            resp = grant(client, token, ct, f"Entity for {ct}")
            assert resp.status_code == 201, f"Failed for {ct}"

    def test_grant_duplicate_rejected(self, client):
        token = register_and_login(client)
        grant(client, token, "healthcare_treatment")
        resp = grant(client, token, "healthcare_treatment")
        assert resp.status_code == 422
        assert "already exists" in resp.get_json()["message"]

    def test_grant_invalid_type(self, client):
        token = register_and_login(client)
        resp = client.post("/api/v1/consents/grant", json={
            "consent_type": "invalid_type",
            "processing_entity_name": "Test",
            "expiry_days": 365,
        }, headers=auth(token))
        assert resp.status_code == 422

    def test_grant_missing_entity_name(self, client):
        token = register_and_login(client)
        resp = client.post("/api/v1/consents/grant", json={
            "consent_type": "healthcare_treatment",
            "processing_entity_name": "",
            "expiry_days": 365,
        }, headers=auth(token))
        assert resp.status_code == 422

    def test_grant_generates_receipt(self, client):
        token = register_and_login(client)
        resp = grant(client, token)
        data = resp.get_json()
        assert data["receipt"]["_id"] is not None
        assert data["receipt"]["action_type"] == "grant"
        assert data["receipt"]["consent_id"] == data["consent"]["_id"]

    def test_grant_with_custom_scope(self, client):
        token = register_and_login(client)
        resp = client.post("/api/v1/consents/grant", json={
            "consent_type": "healthcare_treatment",
            "processing_entity_name": "Custom Entity",
            "expiry_days": 180,
            "custom_scope": ["allergies"],
        }, headers=auth(token))
        assert resp.status_code == 201
        assert resp.get_json()["consent"]["data_categories_in_scope"] == ["allergies"]


class TestListConsents:
    """Test consent listing."""

    def test_list_all_consents(self, client):
        token = register_and_login(client)
        grant(client, token, "healthcare_treatment")
        grant(client, token, "pharmacy_access", "Pharmacy")

        resp = client.get("/api/v1/consents/", headers=auth(token))
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 2

    def test_filter_by_status(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token, "healthcare_treatment")
        consent_id = grant_resp.get_json()["consent"]["_id"]

        # Withdraw one
        client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))

        # Grant another
        grant(client, token, "pharmacy_access", "Pharmacy")

        # Filter active only
        resp = client.get("/api/v1/consents/?status=active", headers=auth(token))
        assert resp.get_json()["count"] == 1

        # Filter withdrawn
        resp = client.get("/api/v1/consents/?status=withdrawn", headers=auth(token))
        assert resp.get_json()["count"] == 1

    def test_filter_by_type(self, client):
        token = register_and_login(client)
        grant(client, token, "healthcare_treatment")
        grant(client, token, "pharmacy_access", "Pharmacy")

        resp = client.get("/api/v1/consents/?type=pharmacy_access", headers=auth(token))
        assert resp.get_json()["count"] == 1
        assert resp.get_json()["consents"][0]["consent_type"] == "pharmacy_access"


class TestGetConsent:
    """Test get single consent."""

    def test_get_own_consent(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        resp = client.get(f"/api/v1/consents/{consent_id}", headers=auth(token))
        assert resp.status_code == 200
        assert resp.get_json()["consent"]["_id"] == consent_id

    def test_cannot_get_other_patient_consent(self, client):
        token1 = register_and_login(client, "p1@test.com")
        grant_resp = grant(client, token1)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        token2 = register_and_login(client, "p2@test.com")
        resp = client.get(f"/api/v1/consents/{consent_id}", headers=auth(token2))
        assert resp.status_code == 403

    def test_get_nonexistent_consent(self, client):
        token = register_and_login(client)
        resp = client.get("/api/v1/consents/nonexistent-id", headers=auth(token))
        assert resp.status_code == 404


class TestModifyConsent:
    """Test consent modification."""

    def test_modify_scope(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        resp = client.put(f"/api/v1/consents/{consent_id}/modify", json={
            "new_scope": ["allergies"],
            "reason": "Restricting to allergies only",
        }, headers=auth(token))

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["consent"]["data_categories_in_scope"] == ["allergies"]
        assert data["consent"]["previous_scope"] is not None
        assert data["consent"]["version"] == 2
        assert data["receipt"]["action_type"] == "modify"

    def test_modify_without_reason_fails(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        resp = client.put(f"/api/v1/consents/{consent_id}/modify", json={
            "new_scope": ["allergies"],
            "reason": "",
        }, headers=auth(token))
        assert resp.status_code == 422

    def test_cannot_modify_withdrawn_consent(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        # Withdraw first
        client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))

        # Try to modify
        resp = client.put(f"/api/v1/consents/{consent_id}/modify", json={
            "new_scope": ["allergies"],
            "reason": "Attempting modify after withdrawal",
        }, headers=auth(token))
        assert resp.status_code == 422


class TestWithdrawConsent:
    """Test consent withdrawal."""

    def test_withdraw_consent(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        resp = client.post(f"/api/v1/consents/{consent_id}/withdraw", json={
            "reason": "No longer need healthcare services",
        }, headers=auth(token))

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["consent"]["status"] == "withdrawn"
        assert data["consent"]["withdrawn_at"] is not None
        assert data["receipt"]["action_type"] == "withdraw"

    def test_withdraw_already_withdrawn_fails(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))
        resp = client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))
        assert resp.status_code == 422

    def test_can_regrant_after_withdrawal(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))

        # Re-grant same type
        resp = grant(client, token, "healthcare_treatment")
        assert resp.status_code == 201


class TestReceipts:
    """Test consent receipts."""

    def test_list_receipts(self, client):
        token = register_and_login(client)
        grant(client, token, "healthcare_treatment")
        grant(client, token, "pharmacy_access", "Pharmacy")

        resp = client.get("/api/v1/consents/receipts", headers=auth(token))
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 2

    def test_get_single_receipt(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        receipt_id = grant_resp.get_json()["receipt"]["_id"]

        resp = client.get(f"/api/v1/consents/receipts/{receipt_id}", headers=auth(token))
        assert resp.status_code == 200
        assert resp.get_json()["receipt"]["action_type"] == "grant"

    def test_receipt_generated_on_withdraw(self, client):
        token = register_and_login(client)
        grant_resp = grant(client, token)
        consent_id = grant_resp.get_json()["consent"]["_id"]

        client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))

        resp = client.get("/api/v1/consents/receipts", headers=auth(token))
        receipts = resp.get_json()["receipts"]
        actions = [r["action_type"] for r in receipts]
        assert "grant" in actions
        assert "withdraw" in actions


class TestActiveSharing:
    """Test active sharing view."""

    def test_active_sharing_shows_only_active(self, client):
        token = register_and_login(client)
        grant(client, token, "healthcare_treatment")
        grant_resp = grant(client, token, "pharmacy_access", "Pharmacy")
        consent_id = grant_resp.get_json()["consent"]["_id"]

        # Withdraw pharmacy
        client.post(f"/api/v1/consents/{consent_id}/withdraw", headers=auth(token))

        resp = client.get("/api/v1/consents/active-sharing", headers=auth(token))
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 1
        assert resp.get_json()["active_sharing"][0]["consent_type"] == "healthcare_treatment"
