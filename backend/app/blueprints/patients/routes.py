"""
Patients Blueprint Routes.

Patient profile management and healthcare record access.
"""

import os
from flask import request, jsonify, g

from app.blueprints.patients import patients_bp
from app.extensions import get_db
from app.config import get_config
from app.services.patient_service import PatientService
from app.services.healthcare_record_service import HealthcareRecordService
from app.middleware.auth_middleware import jwt_required, roles_required


def _get_patient_service():
    return PatientService(get_db())


def _get_record_service():
    return HealthcareRecordService(get_db())


# ─────────────────────────────────────────────────────────────────────
# PATIENT PROFILE
# ─────────────────────────────────────────────────────────────────────

@patients_bp.route("/me", methods=["GET"])
@jwt_required
@roles_required("patient")
def get_my_profile():
    """Get current patient's own profile."""
    svc = _get_patient_service()
    patient = svc.get_patient_by_user_id(g.current_user_id)
    return jsonify({"patient": patient}), 200


@patients_bp.route("/me", methods=["PUT"])
@jwt_required
@roles_required("patient")
def update_my_profile():
    """Update current patient's profile."""
    data = request.get_json() or {}
    svc = _get_patient_service()
    patient = svc.get_patient_by_user_id(g.current_user_id)
    updated = svc.update_patient_profile(patient["_id"], g.current_user_id, data)
    return jsonify({"patient": updated, "message": "Profile updated"}), 200


@patients_bp.route("/", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_all_patients():
    """List all patients (admin only)."""
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 20, type=int)
    svc = _get_patient_service()
    patients = svc.list_all_patients(skip=skip, limit=limit)
    return jsonify({"patients": patients, "count": len(patients)}), 200


@patients_bp.route("/<patient_id>", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_patient_by_id(patient_id):
    """Get a specific patient by ID (admin only)."""
    svc = _get_patient_service()
    patient = svc.get_patient_by_id(patient_id)
    return jsonify({"patient": patient}), 200


# ─────────────────────────────────────────────────────────────────────
# HEALTHCARE RECORDS
# ─────────────────────────────────────────────────────────────────────

@patients_bp.route("/me/records", methods=["GET"])
@jwt_required
@roles_required("patient")
def list_my_records():
    """List current patient's healthcare records."""
    record_type = request.args.get("type")
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 20, type=int)

    svc = _get_record_service()
    records = svc.list_my_records(
        user_id=g.current_user_id,
        record_type=record_type,
        skip=skip,
        limit=limit,
    )
    return jsonify({"records": records, "count": len(records)}), 200


@patients_bp.route("/me/records/<record_id>", methods=["GET"])
@jwt_required
@roles_required("patient")
def get_my_record(record_id):
    """Get a specific healthcare record (own records only)."""
    svc = _get_record_service()
    record = svc.get_record(record_id, g.current_user_id, "patient")
    return jsonify({"record": record}), 200


@patients_bp.route("/me/records", methods=["POST"])
@jwt_required
@roles_required("patient")
def create_my_record():
    """
    Create a healthcare record for the current patient.

    Body:
        {
            "record_type": "consultation",
            "title": "General Checkup",
            "description": "Annual health checkup...",
            "diagnosis_codes": ["Z00.0"],
            "symptoms": ["fatigue"],
            "treatment_notes": "Rest recommended"
        }
    """
    data = request.get_json() or {}
    patient_svc = _get_patient_service()
    patient = patient_svc.get_patient_by_user_id(g.current_user_id)

    svc = _get_record_service()
    record = svc.create_record(
        patient_id=patient["_id"],
        created_by=g.current_user_id,
        record_type=data.get("record_type", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        diagnosis_codes=data.get("diagnosis_codes"),
        symptoms=data.get("symptoms"),
        treatment_notes=data.get("treatment_notes"),
    )
    return jsonify({"record": record, "message": "Record created"}), 201


@patients_bp.route("/me/records/<record_id>", methods=["PUT"])
@jwt_required
@roles_required("patient")
def update_my_record(record_id):
    """Update a healthcare record (own records only)."""
    data = request.get_json() or {}
    svc = _get_record_service()
    record = svc.update_record(record_id, g.current_user_id, "patient", data)
    return jsonify({"record": record, "message": "Record updated"}), 200


# ─────────────────────────────────────────────────────────────────────
# ADMIN ACCESS TO RECORDS
# ─────────────────────────────────────────────────────────────────────

@patients_bp.route("/<patient_id>/records", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_patient_records(patient_id):
    """List records for a specific patient (admin only)."""
    record_type = request.args.get("type")
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 20, type=int)

    svc = _get_record_service()
    records = svc.list_records_for_patient(
        patient_id=patient_id,
        requesting_user_id=g.current_user_id,
        user_role="admin",
        record_type=record_type,
        skip=skip,
        limit=limit,
    )
    return jsonify({"records": records, "count": len(records)}), 200


@patients_bp.route("/<patient_id>/records", methods=["POST"])
@jwt_required
@roles_required("admin")
def create_record_for_patient(patient_id):
    """Create a record for a specific patient (admin only)."""
    data = request.get_json() or {}
    svc = _get_record_service()
    record = svc.create_record(
        patient_id=patient_id,
        created_by=g.current_user_id,
        record_type=data.get("record_type", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        diagnosis_codes=data.get("diagnosis_codes"),
        symptoms=data.get("symptoms"),
        treatment_notes=data.get("treatment_notes"),
    )
    return jsonify({"record": record, "message": "Record created"}), 201
