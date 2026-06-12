"""
Flask Application Factory.

Creates and configures the Flask application with all extensions,
blueprints, middleware, and error handlers.
"""

from flask import Flask
from flask_cors import CORS

from app.config import get_config
from app.extensions import init_extensions


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory pattern.

    Args:
        config_name: Configuration environment (development, testing, production)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config["CORS_ORIGINS"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
        }
    })

    # Initialize extensions (MongoDB, Web3)
    init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": "dpdp-healthcare-api"}, 200

    # MongoDB connectivity test (temporary verification endpoint)
    @app.route("/mongo-test")
    def mongo_test():
        from app.extensions import get_db
        from datetime import datetime, timezone

        db = get_db()
        collection_name = "connection_test"
        collection = db[collection_name]

        # Insert a test document
        test_doc = {
            "status": "working",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "purpose": "MongoDB connectivity verification",
        }
        insert_result = collection.insert_one(test_doc)

        # Read it back
        read_back = collection.find_one({"_id": insert_result.inserted_id})

        # Clean up (remove test document)
        collection.delete_one({"_id": insert_result.inserted_id})

        return {
            "message": "MongoDB Connected",
            "collection": collection_name,
            "inserted_id": str(insert_result.inserted_id),
            "read_back_status": read_back["status"] if read_back else None,
            "verified": read_back is not None and read_back["status"] == "working",
        }, 200

    return app


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.patients import patients_bp
    from app.blueprints.doctors import doctors_bp
    from app.blueprints.pharmacy import pharmacy_bp
    from app.blueprints.consents import consents_bp
    from app.blueprints.audit import audit_bp
    from app.blueprints.blockchain import blockchain_bp
    from app.blueprints.integrity import integrity_bp
    from app.blueprints.compliance import compliance_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(patients_bp, url_prefix="/api/v1/patients")
    app.register_blueprint(doctors_bp, url_prefix="/api/v1/doctors")
    app.register_blueprint(pharmacy_bp, url_prefix="/api/v1/pharmacy")
    app.register_blueprint(consents_bp, url_prefix="/api/v1/consents")
    app.register_blueprint(audit_bp, url_prefix="/api/v1/audit")
    app.register_blueprint(blockchain_bp, url_prefix="/api/v1/blockchain")
    app.register_blueprint(integrity_bp, url_prefix="/api/v1/integrity")
    app.register_blueprint(compliance_bp, url_prefix="/api/v1/compliance")


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""
    from app.utils.errors import (
        AppError,
        handle_app_error,
        handle_validation_error,
        handle_not_found,
        handle_internal_error,
    )

    app.register_error_handler(AppError, handle_app_error)
    app.register_error_handler(400, handle_validation_error)
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(500, handle_internal_error)
