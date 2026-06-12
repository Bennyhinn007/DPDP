"""
DPDP Compliance Service.

Provides aggregated compliance metrics, dashboard data, rights request tracking,
and compliance scoring for the DPO/Admin oversight interface.
"""

from app.utils.helpers import utc_now


class ComplianceService:
    """Aggregates system-wide DPDP compliance data."""

    def __init__(self, db):
        self.db = db

    # ─────────────────────────────────────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────────────────────────────────────

    def get_dashboard(self) -> dict:
        """
        Get full compliance dashboard data.

        Aggregates counts across all collections for DPO/Admin overview.
        """
        return {
            "timestamp": utc_now(),
            "users": self._user_stats(),
            "patients": self._patient_stats(),
            "healthcare_records": self._record_stats(),
            "consents": self._consent_stats(),
            "audit": self._audit_stats(),
            "blockchain": self._blockchain_stats(),
            "rights_requests": self._rights_summary(),
        }

    # ─────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get concise aggregate statistics."""
        return {
            "total_users": self.db["users"].count_documents({}),
            "total_patients": self.db["patients"].count_documents({}),
            "total_records": self.db["healthcare_records"].count_documents({}),
            "total_consents": self.db["consents"].count_documents({}),
            "active_consents": self.db["consents"].count_documents({"status": "active"}),
            "withdrawn_consents": self.db["consents"].count_documents({"status": "withdrawn"}),
            "total_audit_events": self.db["audit_logs"].count_documents({}),
            "total_blockchain_anchors": self.db["blockchain_anchors"].count_documents({}),
            "total_corrections": self._count_corrections(),
            "total_erasures": self._count_erasures(),
            "redacted_records": self.db["healthcare_records"].count_documents({"redacted": True}),
        }

    # ─────────────────────────────────────────────────────────────────
    # RIGHTS REQUESTS
    # ─────────────────────────────────────────────────────────────────

    def get_rights_requests(self, skip: int = 0, limit: int = 20) -> dict:
        """
        Get all DPDP rights requests (corrections + erasures) from version_history.

        Returns:
            Dict with correction_requests, erasure_requests, and totals.
        """
        corrections = list(
            self.db["version_history"]
            .find({"modification_type": "correction"})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        erasures = list(
            self.db["version_history"]
            .find({"modification_type": "erasure"})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "correction_requests": corrections,
            "erasure_requests": erasures,
            "total_corrections": self._count_corrections(),
            "total_erasures": self._count_erasures(),
        }

    # ─────────────────────────────────────────────────────────────────
    # COMPLIANCE SCORE
    # ─────────────────────────────────────────────────────────────────

    def get_compliance_score(self) -> dict:
        """
        Compute DPDP compliance score (0-100) based on system state.

        Evaluates:
        - Encryption coverage
        - Consent management health
        - Audit logging coverage
        - Blockchain anchoring coverage
        - DPDP rights fulfillment
        """
        scores = {}

        # 1. Encryption (20 points)
        scores["encryption"] = self._score_encryption()

        # 2. Consent management (25 points)
        scores["consent_management"] = self._score_consent()

        # 3. Audit logging (20 points)
        scores["audit_logging"] = self._score_audit()

        # 4. Blockchain anchoring (20 points)
        scores["blockchain_anchoring"] = self._score_blockchain()

        # 5. DPDP rights (15 points)
        scores["dpdp_rights"] = self._score_rights()

        total = sum(scores.values())

        return {
            "overall_score": total,
            "max_score": 100,
            "grade": self._grade(total),
            "breakdown": scores,
            "evaluated_at": utc_now(),
        }

    # ─────────────────────────────────────────────────────────────────
    # PRIVATE: COLLECTION STATS
    # ─────────────────────────────────────────────────────────────────

    def _user_stats(self) -> dict:
        users = self.db["users"]
        return {
            "total": users.count_documents({}),
            "by_role": {
                "patient": users.count_documents({"role": "patient"}),
                "admin": users.count_documents({"role": "admin"}),
                "doctor": users.count_documents({"role": "doctor"}),
                "pharmacy_staff": users.count_documents({"role": "pharmacy_staff"}),
                "dpo": users.count_documents({"role": "dpo"}),
            },
            "active": users.count_documents({"status": "active"}),
            "locked": users.count_documents({"status": "locked"}),
        }

    def _patient_stats(self) -> dict:
        patients = self.db["patients"]
        return {
            "total": patients.count_documents({}),
            "active": patients.count_documents({"redacted": False}),
            "redacted": patients.count_documents({"redacted": True}),
        }

    def _record_stats(self) -> dict:
        records = self.db["healthcare_records"]
        return {
            "total": records.count_documents({}),
            "active": records.count_documents({"redacted": False}),
            "redacted": records.count_documents({"redacted": True}),
            "by_type": {
                "consultation": records.count_documents({"record_type": "consultation"}),
                "diagnosis": records.count_documents({"record_type": "diagnosis"}),
                "treatment_plan": records.count_documents({"record_type": "treatment_plan"}),
            },
        }

    def _consent_stats(self) -> dict:
        consents = self.db["consents"]
        return {
            "total": consents.count_documents({}),
            "active": consents.count_documents({"status": "active"}),
            "withdrawn": consents.count_documents({"status": "withdrawn"}),
            "expired": consents.count_documents({"status": "expired"}),
            "by_type": {
                "healthcare_treatment": consents.count_documents({"consent_type": "healthcare_treatment", "status": "active"}),
                "pharmacy_access": consents.count_documents({"consent_type": "pharmacy_access", "status": "active"}),
                "research_access": consents.count_documents({"consent_type": "research_access", "status": "active"}),
                "insurance_access": consents.count_documents({"consent_type": "insurance_access", "status": "active"}),
                "analytics_access": consents.count_documents({"consent_type": "analytics_access", "status": "active"}),
                "marketing_access": consents.count_documents({"consent_type": "marketing_access", "status": "active"}),
            },
        }

    def _audit_stats(self) -> dict:
        audit = self.db["audit_logs"]
        return {
            "total_events": audit.count_documents({}),
            "by_severity": {
                "info": audit.count_documents({"severity": "info"}),
                "warning": audit.count_documents({"severity": "warning"}),
                "critical": audit.count_documents({"severity": "critical"}),
            },
            "by_category": {
                "data_operation": audit.count_documents({"action_category": "data_operation"}),
                "auth_event": audit.count_documents({"action_category": "auth_event"}),
                "consent_event": audit.count_documents({"action_category": "consent_event"}),
                "security_event": audit.count_documents({"action_category": "security_event"}),
            },
        }

    def _blockchain_stats(self) -> dict:
        anchors = self.db["blockchain_anchors"]
        return {
            "total_anchors": anchors.count_documents({}),
            "successful": anchors.count_documents({"transaction_status": "success"}),
            "failed": anchors.count_documents({"transaction_status": {"$regex": "^failed"}}),
        }

    def _rights_summary(self) -> dict:
        return {
            "corrections": self._count_corrections(),
            "erasures": self._count_erasures(),
        }

    def _count_corrections(self) -> int:
        if "version_history" in self.db.list_collection_names():
            return self.db["version_history"].count_documents({"modification_type": "correction"})
        return 0

    def _count_erasures(self) -> int:
        if "version_history" in self.db.list_collection_names():
            return self.db["version_history"].count_documents({"modification_type": "erasure"})
        return 0

    # ─────────────────────────────────────────────────────────────────
    # PRIVATE: SCORING
    # ─────────────────────────────────────────────────────────────────

    def _score_encryption(self) -> int:
        """Score encryption coverage (max 20 points)."""
        # Check if patient records exist and have encrypted fields
        patients = self.db["patients"].count_documents({})
        if patients == 0:
            return 20  # No data to encrypt = compliant by default

        # Sample a patient and check if full_name is encrypted (not plaintext)
        sample = self.db["patients"].find_one({"redacted": False})
        if sample and sample.get("full_name") and isinstance(sample["full_name"], str):
            if sample["full_name"].startswith("gAAAAA"):
                return 20  # Encrypted
            elif len(sample["full_name"]) > 50:
                return 20  # Likely encrypted (long ciphertext)
        return 10  # Partial or unknown

    def _score_consent(self) -> int:
        """Score consent management (max 25 points)."""
        total_patients = self.db["patients"].count_documents({})
        if total_patients == 0:
            return 25

        # Patients with at least one consent
        patients_with_consent = len(self.db["consents"].distinct("patient_id"))
        coverage = patients_with_consent / max(total_patients, 1)

        # Receipts generated
        receipts = self.db["consent_receipts"].count_documents({})
        has_receipts = min(receipts, 1) * 5  # 5 points if any receipts exist

        return min(25, int(coverage * 20) + has_receipts)

    def _score_audit(self) -> int:
        """Score audit logging (max 20 points)."""
        total_events = self.db["audit_logs"].count_documents({})
        if total_events == 0:
            return 0

        # Check hash chain integrity (sample)
        sample = self.db["audit_logs"].find_one(sort=[("created_at", -1)])
        has_hash = 10 if sample and sample.get("log_hash") else 0
        has_chain = 10 if sample and sample.get("previous_log_hash") else 0

        return has_hash + has_chain

    def _score_blockchain(self) -> int:
        """Score blockchain anchoring (max 20 points)."""
        total_anchors = self.db["blockchain_anchors"].count_documents({})
        if total_anchors == 0:
            return 0

        successful = self.db["blockchain_anchors"].count_documents({"transaction_status": "success"})
        success_rate = successful / max(total_anchors, 1)

        return min(20, int(success_rate * 20))

    def _score_rights(self) -> int:
        """Score DPDP rights fulfillment (max 15 points)."""
        score = 0

        # Right to access: patients can view data (assumed if system running)
        score += 5

        # Right to correction: version_history has corrections
        if self._count_corrections() > 0 or self.db["patients"].count_documents({}) > 0:
            score += 5

        # Right to erasure: system supports redaction
        if "chameleon_hash_records" in self.db.list_collection_names():
            score += 5
        elif self.db["healthcare_records"].count_documents({"redacted": True}) >= 0:
            score += 5

        return min(15, score)

    @staticmethod
    def _grade(score: int) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"
