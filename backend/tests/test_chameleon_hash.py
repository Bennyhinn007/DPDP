"""
Tests for Chameleon Hash Simulation Layer.

Demonstrates and verifies all five required behaviors:
1. Controlled Modification
2. Authorized Redaction
3. Version Preservation
4. Audit Trail Preservation
5. Blockchain Verification
"""

import pytest
from app.services.chameleon_hash_service import (
    ChameleonHashSimulator,
    RedactionType,
    AuthorizationStatus,
)


@pytest.fixture
def simulator():
    """Create a ChameleonHashSimulator instance."""
    return ChameleonHashSimulator()


@pytest.fixture
def sample_patient_record():
    """A sample patient record as stored in MongoDB."""
    return {
        "_id": "pat-1234-abcd-efgh-ijkl-mnop",
        "user_id": "user-1234",
        "full_name": "Rajesh Kumar",
        "phone_number": "+91-9876543210",
        "address": "21 Greams Lane, Chennai, Tamil Nadu 600006",
        "identity_type": "aadhaar",
        "identity_number": "1234-5678-9012",
        "blood_group": "O+",
        "allergies": ["Penicillin"],
        "version": 1,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
        "created_by": "user-1234",
        "updated_by": "user-1234",
        "verification_hash": None,
        "blockchain_tx_ref": None,
        "blockchain_anchor_id": None,
        "redacted": False,
        "redacted_at": None,
        "redacted_by": None,
        "redaction_reason": None,
    }


@pytest.fixture
def sample_healthcare_record():
    """A sample healthcare record."""
    return {
        "_id": "hr-4001-abcd-efgh-ijkl-mnop",
        "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
        "doctor_id": "doc-5678",
        "record_type": "consultation",
        "title": "Cardiology Consultation",
        "description": "Patient presents with chest pain and shortness of breath.",
        "diagnosis_codes": ["I25.1", "R07.9"],
        "symptoms": ["chest_pain", "shortness_of_breath"],
        "treatment_notes": "Prescribed Aspirin 75mg daily. Follow-up in 4 weeks.",
        "version": 1,
        "created_at": "2025-06-10T11:30:00Z",
        "updated_at": "2025-06-10T11:30:00Z",
        "created_by": "doc-5678",
        "updated_by": "doc-5678",
        "verification_hash": None,
        "blockchain_tx_ref": None,
        "blockchain_anchor_id": None,
        "redacted": False,
        "redacted_at": None,
        "redacted_by": None,
        "redaction_reason": None,
    }


class TestHashComputation:
    """Test deterministic hash computation."""

    def test_same_data_produces_same_hash(self, simulator, sample_patient_record):
        hash1 = simulator.compute_record_hash(sample_patient_record)
        hash2 = simulator.compute_record_hash(sample_patient_record)
        assert hash1 == hash2

    def test_different_data_produces_different_hash(self, simulator, sample_patient_record):
        hash1 = simulator.compute_record_hash(sample_patient_record)
        modified = dict(sample_patient_record)
        modified["full_name"] = "Rajesh Kumar Modified"
        hash2 = simulator.compute_record_hash(modified)
        assert hash1 != hash2

    def test_metadata_fields_excluded_from_hash(self, simulator, sample_patient_record):
        hash1 = simulator.compute_record_hash(sample_patient_record)
        modified = dict(sample_patient_record)
        modified["updated_at"] = "2025-12-01T00:00:00Z"
        modified["version"] = 99
        hash2 = simulator.compute_record_hash(modified)
        assert hash1 == hash2

    def test_hash_is_valid_sha256(self, simulator, sample_patient_record):
        h = simulator.compute_record_hash(sample_patient_record)
        assert len(h) == 64  # SHA-256 hex = 64 chars
        assert all(c in "0123456789abcdef" for c in h)


class TestControlledModification:
    """Test Behavior 1: Controlled Modification — only authorized actors can modify."""

    def test_unauthorized_role_cannot_authorize(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Phone number changed",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )

        with pytest.raises(PermissionError, match="Only DPO or Admin"):
            simulator.authorize_redaction(
                request,
                authorizer_id="doc-5678",
                authorizer_role="doctor",
                legal_basis="Section 12",
            )

    def test_dpo_can_authorize(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Phone number changed",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )

        authorized = simulator.authorize_redaction(
            request,
            authorizer_id="dpo-0001",
            authorizer_role="dpo",
            legal_basis="DPDP Act Section 12 - Right to Correction",
        )

        assert authorized["status"] == AuthorizationStatus.AUTHORIZED.value
        assert authorized["authorized_by"] == "dpo-0001"
        assert authorized["legal_basis"] == "DPDP Act Section 12 - Right to Correction"

    def test_cannot_execute_without_authorization(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Phone number changed",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )

        with pytest.raises(ValueError, match="must be AUTHORIZED"):
            simulator.execute_correction(
                request,
                sample_patient_record,
                {"phone_number": "+91-1111111111"},
            )


class TestAuthorizedRedaction:
    """Test Behavior 2: Authorized Redaction (erasure)."""

    def test_erasure_replaces_fields_with_redacted(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.ERASURE,
            reason="Patient exercised right to erasure",
            requested_by="user-1234",
            affected_fields=["full_name", "phone_number", "address", "identity_number"],
        )

        simulator.authorize_redaction(
            request,
            authorizer_id="dpo-0001",
            authorizer_role="dpo",
            legal_basis="DPDP Act Section 12 - Right to Erasure",
        )

        result = simulator.execute_erasure(
            request,
            sample_patient_record,
            fields_to_redact=["full_name", "phone_number", "address", "identity_number"],
        )

        modified = result["modified_record"]
        assert modified["full_name"] == "[REDACTED]"
        assert modified["phone_number"] == "[REDACTED]"
        assert modified["address"] == "[REDACTED]"
        assert modified["identity_number"] == "[REDACTED]"
        assert modified["redacted"] is True
        assert modified["redaction_reason"] == "DPDP Act Section 12 - Right to Erasure"

    def test_erasure_preserves_non_redacted_fields(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.ERASURE,
            reason="Partial erasure",
            requested_by="user-1234",
            affected_fields=["full_name"],
        )

        simulator.authorize_redaction(
            request, "dpo-0001", "dpo", "DPDP Section 12"
        )

        result = simulator.execute_erasure(
            request, sample_patient_record, ["full_name"]
        )

        modified = result["modified_record"]
        assert modified["full_name"] == "[REDACTED]"
        assert modified["blood_group"] == "O+"  # Unaffected
        assert modified["allergies"] == ["Penicillin"]  # Unaffected


class TestVersionPreservation:
    """Test Behavior 3: Version Preservation — previous state archived."""

    def test_correction_creates_version_archive(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Phone number changed",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )
        simulator.authorize_redaction(request, "dpo-0001", "dpo", "Section 12")

        result = simulator.execute_correction(
            request, sample_patient_record, {"phone_number": "+91-9999999999"}
        )

        archive = result["version_archive"]
        assert archive["resource_id"] == sample_patient_record["_id"]
        assert archive["version_number"] == 1
        assert archive["record_snapshot"]["phone_number"] == "+91-9876543210"
        assert archive["modification_type"] == "correction"
        assert archive["legal_basis"] == "Section 12"

    def test_version_number_increments(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Update",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )
        simulator.authorize_redaction(request, "dpo-0001", "dpo", "Section 12")

        result = simulator.execute_correction(
            request, sample_patient_record, {"phone_number": "+91-1111111111"}
        )

        assert result["modified_record"]["version"] == 2


class TestAuditTrailPreservation:
    """Test Behavior 4: Audit Trail Preservation — full audit through redaction."""

    def test_correction_generates_audit_entry(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Correct phone number",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )
        simulator.authorize_redaction(request, "dpo-0001", "dpo", "Section 12")

        result = simulator.execute_correction(
            request, sample_patient_record, {"phone_number": "+91-5555555555"}
        )

        audit = result["audit_entry"]
        assert audit["action_type"] == "chameleon_correction"
        assert audit["action_category"] == "compliance_event"
        assert audit["actor_id"] == "dpo-0001"
        assert audit["details"]["original_hash"] == result["original_hash"]
        assert audit["details"]["modified_hash"] == result["modified_hash"]
        assert audit["details"]["redaction_proof_hash"] == result["redaction_proof_hash"]
        assert audit["details"]["legal_basis"] == "Section 12"

    def test_erasure_generates_audit_entry(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.ERASURE,
            reason="Right to erasure exercised",
            requested_by="user-1234",
            affected_fields=["full_name", "phone_number"],
        )
        simulator.authorize_redaction(request, "dpo-0001", "dpo", "Section 12")

        result = simulator.execute_erasure(
            request, sample_patient_record, ["full_name", "phone_number"]
        )

        audit = result["audit_entry"]
        assert audit["action_type"] == "chameleon_erasure"
        assert "full_name" in audit["details"]["affected_fields"]
        assert "phone_number" in audit["details"]["affected_fields"]

    def test_audit_entry_contains_proof_hash(self, simulator, sample_patient_record):
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Correction",
            requested_by="user-1234",
            affected_fields=["blood_group"],
        )
        simulator.authorize_redaction(request, "dpo-0001", "dpo", "Section 12")

        result = simulator.execute_correction(
            request, sample_patient_record, {"blood_group": "A+"}
        )

        # The proof hash must be present in the audit for traceability
        assert result["audit_entry"]["details"]["redaction_proof_hash"] is not None
        assert len(result["audit_entry"]["details"]["redaction_proof_hash"]) == 64


class TestBlockchainVerification:
    """Test Behavior 5: Blockchain Verification — simulated chameleon property."""

    def test_unmodified_record_verified(self, simulator, sample_patient_record):
        """Record unchanged since anchoring → VERIFIED."""
        blockchain_hash = simulator.compute_record_hash(sample_patient_record)

        result = simulator.verify_record_integrity(
            sample_patient_record, blockchain_hash
        )

        assert result["status"] == "VERIFIED"
        assert result["modification_detected"] is False

    def test_unauthorized_modification_detected(self, simulator, sample_patient_record):
        """Record modified without authorization → INTEGRITY_VIOLATION."""
        blockchain_hash = simulator.compute_record_hash(sample_patient_record)

        # Simulate unauthorized tampering
        tampered_record = dict(sample_patient_record)
        tampered_record["full_name"] = "Hacker Modified Name"

        result = simulator.verify_record_integrity(
            tampered_record, blockchain_hash, redaction_proofs=[]
        )

        assert result["status"] == "INTEGRITY_VIOLATION"
        assert result["modification_detected"] is True
        assert result["authorized_modification"] is False

    def test_authorized_modification_verified(self, simulator, sample_patient_record):
        """Record modified with authorization → VERIFIED_MODIFIED (chameleon property)."""
        # Anchor original hash on blockchain
        blockchain_hash = simulator.compute_record_hash(sample_patient_record)

        # Execute authorized correction
        request = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Phone correction",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )
        simulator.authorize_redaction(request, "dpo-0001", "dpo", "Section 12")
        result = simulator.execute_correction(
            request, sample_patient_record, {"phone_number": "+91-0000000000"}
        )

        # Verify the modified record against the ORIGINAL blockchain hash
        # This is the key Chameleon Hash property:
        # Despite the hash mismatch, the proof chain makes it valid
        verification = simulator.verify_record_integrity(
            current_record=result["modified_record"],
            blockchain_stored_hash=blockchain_hash,
            redaction_proofs=[result["redaction_request"]],
        )

        assert verification["status"] == "VERIFIED_MODIFIED"
        assert verification["authorized_modification"] is True
        assert len(verification["proof_chain"]) == 1
        assert verification["proof_chain"][0]["authorized_by"] == "dpo-0001"

    def test_multi_step_redaction_chain(self, simulator, sample_patient_record):
        """Multiple successive modifications verified via proof chain."""
        # Original blockchain anchor
        blockchain_hash = simulator.compute_record_hash(sample_patient_record)

        # First correction
        req1 = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Phone correction",
            requested_by="user-1234",
            affected_fields=["phone_number"],
        )
        simulator.authorize_redaction(req1, "dpo-0001", "dpo", "Section 12")
        result1 = simulator.execute_correction(
            req1, sample_patient_record, {"phone_number": "+91-1111111111"}
        )

        # Second correction (on the already-modified record)
        req2 = simulator.create_redaction_request(
            resource_type="patients",
            resource_id=sample_patient_record["_id"],
            patient_id=sample_patient_record["_id"],
            redaction_type=RedactionType.CORRECTION,
            reason="Address correction",
            requested_by="user-1234",
            affected_fields=["address"],
        )
        simulator.authorize_redaction(req2, "dpo-0001", "dpo", "Section 12")
        result2 = simulator.execute_correction(
            req2, result1["modified_record"], {"address": "New Address, Mumbai"}
        )

        # Verify final record against ORIGINAL blockchain hash
        # Needs both proofs in the chain
        verification = simulator.verify_record_integrity(
            current_record=result2["modified_record"],
            blockchain_stored_hash=blockchain_hash,
            redaction_proofs=[
                result1["redaction_request"],
                result2["redaction_request"],
            ],
        )

        assert verification["status"] == "VERIFIED_MODIFIED"
        assert len(verification["proof_chain"]) == 2


class TestComparisonDisplay:
    """Test the Traditional vs Chameleon Hash comparison data generation."""

    def test_comparison_shows_both_approaches(self, simulator, sample_patient_record):
        modified = dict(sample_patient_record)
        modified["full_name"] = "Modified Name"

        comparison = simulator.generate_comparison_data(
            sample_patient_record, modified
        )

        # Traditional hash shows chain broken
        assert comparison["traditional_hash"]["hashes_match"] is False
        assert comparison["traditional_hash"]["chain_valid"] is False

        # Chameleon simulation shows chain valid (with proof)
        assert comparison["chameleon_hash_simulation"]["hashes_match"] is False
        assert comparison["chameleon_hash_simulation"]["chain_valid"] is True
        assert "formula_reference" in comparison["chameleon_hash_simulation"]
