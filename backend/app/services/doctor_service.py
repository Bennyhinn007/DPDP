"""
Doctor Service.

Provides consent-gated access to patient healthcare records.
Every access attempt is audited regardless of outcome.
"""

from app.utils.helpers import generate_uuid, utc_now
from app.utils.errors import NotFoundError, AuthorizationError, ConsentRequiredError
from app.services.encryption_service import get_encryption_service
from app.services.consent_service import ConsentService
from app.services.audit_service import AuditService


class DoctorService:
    """Manages doctor's consent-gated access to patient data."""

    def __init__(self, db):
        self.db = db
        self.patients = db["patients"]
        self.records = db["healthcare_records"]
        self.users = db["users"]
        self.enc = get_encryption_service()
        self.consent_svc = ConsentService(db)
        self.audit_svc = AuditService(db)

    def search_patients(self, query: str, doctor_id: str) -> list:
        """
        Search patients by name (decrypted match).

        Returns basic patient info without sensitive data.
        Does NOT require consent (searching ≠ accessing records).
        """
        # Get all non-redacted patients
        patients = list(self.patients.find({"redacted": False}).limit(50))
        results = []

        for p in patients:
            decrypted = self.enc.decrypt_document(p)
            name = decrypted.get("full_name", "")
            if name and query.lower() in name.lower():
                results.append({
                    "_id": p["_id"],
                    "user_id": p["user_id"],
                    "full_name": name,
                    "has_treatment_consent": self._has_consent(p["_id"]),
                })

        # Audit the search
        self.audit_svc.log_event(
            actor_id=doctor_id,
            actor_role="doctor",
            action_type="read",
            resource_type="patients",
            reason=f"Patient search: '{query}'",
            details={"search_query": query, "results_count": len(results)},
        )

        return results

    def get_patient_records(
        self, patient_id: str, doctor_id: str, doctor_name: str
    ) -> dict:
        """
        Access patient's healthcare records (consent-gated).

        Requires active 'healthcare_treatment' consent from the patient.
        Every attempt is audited.

        Returns:
            Dict with records if consent exists, or denial info

        Raises:
            ConsentRequiredError: No active consent for this patient
        """
        # Get patient
        patient = self.patients.find_one({"_id": patient_id})
        if not patient:
            raise NotFoundError("Patient not found")

        patient_decrypted = self.enc.decrypt_document(patient)

        # Check consent
        consent = self.consent_svc.get_active_consent(patient_id, "healthcare_treatment")

        if not consent:
            # Audit the DENIED access
            self.audit_svc.log_event(
                actor_id=doctor_id,
                actor_role="doctor",
                action_type="read",
                resource_type="healthcare_records",
                patient_id=patient["user_id"],
                reason="Access DENIED: No active healthcare_treatment consent",
                severity="warning",
                details={"patient_id": patient_id, "consent_status": "absent"},
            )
            raise ConsentRequiredError(
                f"Patient '{patient_decrypted.get('full_name', 'Unknown')}' has not granted "
                f"healthcare treatment consent. Access denied per DPDP Act."
            )

        # Consent exists — fetch records
        records_raw = list(
            self.records.find({"patient_id": patient_id, "redacted": False})
            .sort("created_at", -1)
            .limit(20)
        )
        records = [self.enc.decrypt_document(r) for r in records_raw]

        # Audit the GRANTED access
        self.audit_svc.log_event(
            actor_id=doctor_id,
            actor_role="doctor",
            action_type="read",
            resource_type="healthcare_records",
            patient_id=patient["user_id"],
            reason="Access GRANTED: Valid healthcare_treatment consent",
            details={
                "patient_id": patient_id,
                "consent_id": consent["_id"],
                "records_accessed": len(records),
            },
        )

        # Log data access for patient timeline
        self.audit_svc.log_data_access(
            patient_id=patient["user_id"],
            accessor_id=doctor_id,
            accessor_role="doctor",
            accessor_name=doctor_name,
            access_type="view",
            data_categories=["medical_history", "allergies", "prescriptions"],
            purpose="Healthcare treatment consultation",
            consent_id=consent["_id"],
        )

        return {
            "patient": {
                "_id": patient_id,
                "full_name": patient_decrypted.get("full_name"),
                "blood_group": patient_decrypted.get("blood_group"),
                "allergies": patient_decrypted.get("allergies", []),
            },
            "consent": {
                "_id": consent["_id"],
                "consent_type": consent["consent_type"],
                "granted_at": consent["granted_at"],
                "expires_at": consent["expires_at"],
            },
            "records": records,
            "access_status": "granted",
        }

    def _has_consent(self, patient_id: str) -> bool:
        """Check if patient has active healthcare treatment consent."""
        consent = self.consent_svc.get_active_consent(patient_id, "healthcare_treatment")
        return consent is not None
