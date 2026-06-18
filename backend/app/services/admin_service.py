"""
Admin Service — Identity & Access Governance.

Aggregates user identity data, access patterns, risk levels,
and healthcare relationships for the governance dashboard.
"""

from datetime import datetime, timezone, timedelta
from app.utils.helpers import utc_now
from app.services.encryption_service import get_encryption_service


class AdminService:
    """Provides user governance data aggregation."""

    def __init__(self, db):
        self.db = db
        self.users = db["users"]
        self.patients = db["patients"]
        self.consents = db["consents"]
        self.records = db["healthcare_records"]
        self.audit_logs = db["audit_logs"]
        self.enc = get_encryption_service()

    def get_governance_data(self) -> dict:
        """
        Aggregate full governance dataset for the Identity Center.

        Returns user directory, lifecycle metrics, access security,
        and healthcare relationships.
        """
        now = datetime.now(timezone.utc)
        day_ago = (now - timedelta(hours=24)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        # Lifecycle metrics
        total = self.users.count_documents({})
        active_today = self.users.count_documents({"last_login": {"$gte": day_ago}})
        patients_count = self.users.count_documents({"role": "patient"})
        doctors_count = self.users.count_documents({"role": "doctor"})
        admins_count = self.users.count_documents({"role": {"$in": ["admin", "dpo"]}})
        locked = self.users.count_documents({"locked_until": {"$ne": None}})
        dormant = self.users.count_documents({
            "last_login": {"$lt": thirty_days_ago, "$ne": None}
        })
        never_logged = self.users.count_documents({"last_login": None})

        # Access security
        failed_attempts_users = self.users.count_documents({"failed_login_attempts": {"$gt": 0}})

        # Healthcare relationships
        patients_with_consent = len(self.consents.distinct("patient_id", {"status": "active"}))
        total_patients_profiles = self.patients.count_documents({"redacted": False})
        patients_without_consent = max(0, total_patients_profiles - patients_with_consent)

        # Doctor access events (last 7 days)
        week_ago = (now - timedelta(days=7)).isoformat()
        doctor_access_events = self.audit_logs.count_documents({
            "actor_role": "doctor",
            "action_type": "read",
            "created_at": {"$gte": week_ago},
        })

        # User directory
        users_list = self._build_user_directory()

        return {
            "metrics": {
                "total_users": total,
                "active_today": active_today,
                "patients": patients_count,
                "doctors": doctors_count,
                "admins": admins_count,
                "locked": locked,
                "dormant": dormant,
                "never_logged_in": never_logged,
                "failed_login_attempts_users": failed_attempts_users,
                "patients_with_consent": patients_with_consent,
                "patients_without_consent": patients_without_consent,
                "doctor_access_events_7d": doctor_access_events,
            },
            "users": users_list,
            "generated_at": utc_now(),
        }

    def _build_user_directory(self) -> list:
        """Build user directory with risk levels and activity counts."""
        users_raw = list(self.users.find().sort("created_at", -1).limit(50))
        directory = []

        for u in users_raw:
            user_id = u["_id"]

            # Get record/consent counts for patients
            records_count = 0
            consents_count = 0
            if u.get("role") == "patient":
                patient = self.patients.find_one({"user_id": user_id})
                if patient:
                    records_count = self.records.count_documents({"patient_id": patient["_id"]})
                    consents_count = self.consents.count_documents({
                        "patient_id": patient["_id"], "status": "active"
                    })

            # Compute risk level
            risk = self._compute_risk(u, consents_count)

            # Decrypt name
            full_name = u.get("full_name", "Unknown")

            directory.append({
                "id": user_id,
                "full_name": full_name,
                "email": u.get("email_encrypted", ""),
                "role": u.get("role", "unknown"),
                "status": self._user_status(u),
                "last_login": u.get("last_login"),
                "failed_login_attempts": u.get("failed_login_attempts", 0),
                "records_count": records_count,
                "consents_count": consents_count,
                "risk_level": risk,
                "created_at": u.get("created_at"),
            })

        return directory

    def _compute_risk(self, user: dict, consents_count: int) -> str:
        """Compute identity risk level based on user behavior."""
        score = 0

        # Failed logins
        failures = user.get("failed_login_attempts", 0)
        if failures >= 3:
            score += 3
        elif failures > 0:
            score += 1

        # Locked account
        if user.get("locked_until"):
            score += 2

        # Dormancy
        last_login = user.get("last_login")
        if last_login:
            try:
                login_dt = datetime.fromisoformat(last_login)
                days_inactive = (datetime.now(timezone.utc) - login_dt).days
                if days_inactive > 30:
                    score += 2
                elif days_inactive > 14:
                    score += 1
            except (ValueError, TypeError):
                pass
        elif user.get("role") == "patient":
            score += 1  # Never logged in

        # Missing consent (patients only)
        if user.get("role") == "patient" and consents_count == 0:
            score += 2

        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        return "low"

    @staticmethod
    def _user_status(user: dict) -> str:
        """Determine display status."""
        if user.get("locked_until"):
            return "locked"
        if user.get("status") == "suspended":
            return "suspended"
        return "active"
