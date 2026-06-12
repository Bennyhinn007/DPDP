"""
Audit Logging Service.

Generates immutable audit log entries for every data operation.
Provides patient-facing timeline and DPO oversight APIs.

Every action in the system produces an audit entry containing:
- Actor identity and role
- Timestamp
- Action type and category
- Affected resource
- Patient ID (if applicable)
- Severity level
- Request metadata (IP, user agent)
"""

import hashlib
import json
from typing import Optional

from app.utils.helpers import generate_uuid, utc_now
from app.utils.errors import NotFoundError, AuthorizationError
from app.utils.constants import AuditActionType, AuditSeverity


class AuditService:
    """Manages audit log generation and retrieval."""

    def __init__(self, db):
        self.db = db
        self.audit_logs = db["audit_logs"]
        self.data_access_logs = db["data_access_logs"]

    # ─────────────────────────────────────────────────────────────────
    # LOG CREATION
    # ─────────────────────────────────────────────────────────────────

    def log_event(
        self,
        actor_id: str,
        actor_role: str,
        action_type: str,
        resource_type: str,
        resource_id: str = None,
        patient_id: str = None,
        reason: str = None,
        details: dict = None,
        severity: str = "info",
        source_ip: str = None,
        user_agent: str = None,
    ) -> dict:
        """
        Create an immutable audit log entry.

        Args:
            actor_id: UUID of the user performing the action
            actor_role: Role of the actor at time of action
            action_type: Type of action (from AuditActionType)
            resource_type: Collection/entity affected
            resource_id: UUID of affected document
            patient_id: UUID of affected patient (if applicable)
            reason: Stated reason for the action
            details: Additional action-specific metadata
            severity: Event severity (info, warning, critical)
            source_ip: Request source IP
            user_agent: Client user agent

        Returns:
            Created audit log document
        """
        log_id = generate_uuid()
        now = utc_now()

        # Compute hash chain link
        previous_log = self.audit_logs.find_one(
            sort=[("created_at", -1)]
        )
        previous_log_hash = previous_log["log_hash"] if previous_log else "genesis"

        # Compute this entry's hash
        log_content = {
            "actor_id": actor_id,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "patient_id": patient_id,
            "timestamp": now,
            "previous_log_hash": previous_log_hash,
        }
        log_hash = hashlib.sha256(
            json.dumps(log_content, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        log_doc = {
            "_id": log_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action_type": action_type,
            "action_category": self._categorize_action(action_type),
            "severity": severity,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "patient_id": patient_id,
            "reason": reason or self._default_reason(action_type),
            "details": details or {},
            "source_ip": source_ip,
            "user_agent": user_agent,
            "log_hash": log_hash,
            "previous_log_hash": previous_log_hash,
            "blockchain_tx_ref": None,
            "blockchain_anchor_id": None,
            "tampered": False,
            "created_at": now,
        }

        self.audit_logs.insert_one(log_doc)
        return log_doc

    def log_data_access(
        self,
        patient_id: str,
        accessor_id: str,
        accessor_role: str,
        accessor_name: str,
        access_type: str,
        data_categories: list,
        purpose: str,
        consent_id: str = None,
    ) -> dict:
        """
        Create a patient-facing data access log entry.

        This is the materialized view used for the Data Usage Timeline.

        Args:
            patient_id: UUID of the patient whose data was accessed
            accessor_id: UUID of the user who accessed data
            accessor_role: Role of the accessor
            accessor_name: Display name of accessor
            access_type: Type of access (view, download, modify, emergency)
            data_categories: List of categories accessed
            purpose: Stated reason for access
            consent_id: UUID of authorizing consent (if any)

        Returns:
            Created data access log document
        """
        log_id = generate_uuid()
        now = utc_now()

        access_doc = {
            "_id": log_id,
            "patient_id": patient_id,
            "accessor_id": accessor_id,
            "accessor_role": accessor_role,
            "accessor_name": accessor_name,
            "access_type": access_type,
            "data_categories": data_categories,
            "purpose": purpose,
            "consent_id": consent_id,
            "access_timestamp": now,
            "created_at": now,
        }

        self.data_access_logs.insert_one(access_doc)
        return access_doc

    # ─────────────────────────────────────────────────────────────────
    # PATIENT TIMELINE
    # ─────────────────────────────────────────────────────────────────

    def get_patient_timeline(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        action_type: str = None,
    ) -> list:
        """
        Get audit timeline for a specific patient.

        Shows all events related to a patient's data in reverse chronological order.

        Args:
            patient_id: UUID of the patient
            skip: Pagination offset
            limit: Max results
            action_type: Filter by action type (optional)

        Returns:
            List of audit log entries affecting this patient
        """
        query = {"patient_id": patient_id}
        if action_type:
            query["action_type"] = action_type

        return list(
            self.audit_logs.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

    def get_data_access_history(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        accessor_role: str = None,
        data_category: str = None,
    ) -> list:
        """
        Get data access history for a patient (who accessed what and when).

        This feeds the Data Usage Timeline UI.

        Args:
            patient_id: UUID of the patient
            skip: Pagination offset
            limit: Max results
            accessor_role: Filter by role (optional)
            data_category: Filter by data category (optional)

        Returns:
            List of data access log entries
        """
        query = {"patient_id": patient_id}
        if accessor_role:
            query["accessor_role"] = accessor_role
        if data_category:
            query["data_categories"] = data_category

        return list(
            self.data_access_logs.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

    def get_timeline_summary(self, patient_id: str) -> dict:
        """
        Get summary statistics for patient timeline.

        Returns:
            Dict with counts per time period
        """
        total = self.data_access_logs.count_documents({"patient_id": patient_id})
        return {
            "total_access_events": total,
            "patient_id": patient_id,
        }

    # ─────────────────────────────────────────────────────────────────
    # DPO / ADMIN OVERVIEW
    # ─────────────────────────────────────────────────────────────────

    def get_all_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        action_type: str = None,
        severity: str = None,
        actor_id: str = None,
        resource_type: str = None,
    ) -> list:
        """
        Get all audit logs (DPO/Admin access).

        Args:
            skip: Pagination offset
            limit: Max results
            action_type: Filter by action type
            severity: Filter by severity
            actor_id: Filter by actor
            resource_type: Filter by resource type

        Returns:
            List of audit log entries
        """
        query = {}
        if action_type:
            query["action_type"] = action_type
        if severity:
            query["severity"] = severity
        if actor_id:
            query["actor_id"] = actor_id
        if resource_type:
            query["resource_type"] = resource_type

        return list(
            self.audit_logs.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

    def get_log_by_id(self, log_id: str) -> dict:
        """Get a single audit log entry."""
        log = self.audit_logs.find_one({"_id": log_id})
        if not log:
            raise NotFoundError("Audit log entry not found")
        return log

    def get_audit_stats(self) -> dict:
        """Get aggregate audit statistics for DPO dashboard."""
        total = self.audit_logs.count_documents({})
        critical = self.audit_logs.count_documents({"severity": "critical"})
        warnings = self.audit_logs.count_documents({"severity": "warning"})
        return {
            "total_events": total,
            "critical_events": critical,
            "warning_events": warnings,
        }

    # ─────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _categorize_action(action_type: str) -> str:
        """Map action type to category."""
        auth_actions = {"login", "logout"}
        consent_actions = {"consent_grant", "consent_withdraw", "consent_modify"}
        security_actions = {"break_glass", "redaction"}
        if action_type in auth_actions:
            return "auth_event"
        if action_type in consent_actions:
            return "consent_event"
        if action_type in security_actions:
            return "security_event"
        return "data_operation"

    @staticmethod
    def _default_reason(action_type: str) -> str:
        """Generate default reason if none provided."""
        reasons = {
            "create": "Record created",
            "read": "Data accessed",
            "update": "Record updated",
            "delete": "Record deleted",
            "login": "User authentication",
            "logout": "User session ended",
            "consent_grant": "Consent granted by data principal",
            "consent_withdraw": "Consent withdrawn by data principal",
            "consent_modify": "Consent scope modified by data principal",
            "verification": "Integrity verification performed",
            "export": "Data exported by data principal",
        }
        return reasons.get(action_type, "System operation")
