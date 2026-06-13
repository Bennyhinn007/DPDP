"""
Swagger/OpenAPI Configuration.

Provides API documentation at /api/docs.
"""

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "DPDP Healthcare Platform API",
        "description": (
            "DPDP-Compliant Redactable Blockchain Based Healthcare & Pharmacy Management System.\n\n"
            "## Features\n"
            "- JWT Authentication with RBAC (Patient, Doctor, Admin)\n"
            "- AES-256 Field-Level Encryption\n"
            "- Blockchain Hash Anchoring (Ganache/Ethereum)\n"
            "- Chameleon Hash Simulation for Redactable Blockchain\n"
            "- DPDP Right to Correction & Erasure\n"
            "- Consent Lifecycle Management\n"
            "- Immutable Audit Trail with Hash Chain\n"
            "- Compliance Scoring Engine\n\n"
            "## Authentication\n"
            "Use `POST /api/v1/auth/login` to obtain a JWT token.\n"
            "Include the token in the `Authorization: Bearer <token>` header."
        ),
        "version": "1.0.0",
        "contact": {
            "name": "DPDP Healthcare Team",
        },
    },
    "host": "localhost:5000",
    "basePath": "/api/v1",
    "schemes": ["http"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token. Format: Bearer {token}",
        }
    },
    "tags": [
        {"name": "Auth", "description": "Authentication & Registration"},
        {"name": "Patients", "description": "Patient Profile & Healthcare Records"},
        {"name": "Consents", "description": "DPDP Consent Lifecycle"},
        {"name": "Doctors", "description": "Consent-Gated Patient Access"},
        {"name": "Audit", "description": "Audit Timeline & DPO Oversight"},
        {"name": "Integrity", "description": "Blockchain Verification"},
        {"name": "Compliance", "description": "DPDP Compliance Dashboard"},
        {"name": "Blockchain", "description": "Blockchain Network Status"},
    ],
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/api/docs/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/api/docs/static",
    "swagger_ui": True,
    "specs_route": "/api/docs/",
}
