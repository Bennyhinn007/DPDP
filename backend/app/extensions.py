"""
Application Extensions.

Initializes MongoDB client and Web3 connection.
These are configured once and shared across the application.
"""

from flask import Flask
from pymongo import MongoClient

# Global instances (initialized in init_extensions)
mongo_client: MongoClient = None
db = None
w3 = None


def init_extensions(app: Flask) -> None:
    """
    Initialize all application extensions.

    Args:
        app: Flask application instance
    """
    global mongo_client, db, w3

    # MongoDB
    mongo_client = MongoClient(app.config["MONGO_URI"])
    db = mongo_client[app.config["MONGO_DB_NAME"]]

    # Web3 (Ganache)
    try:
        from web3 import Web3
        provider = Web3.HTTPProvider(
            app.config["GANACHE_URL"],
            request_kwargs={"timeout": 3}
        )
        w3 = Web3(provider)
    except Exception:
        w3 = None

    # Set encryption key in environment if configured
    if app.config.get("ENCRYPTION_KEY"):
        import os
        os.environ["ENCRYPTION_KEY"] = app.config["ENCRYPTION_KEY"]
        # Reset singleton so it picks up the new key
        from app.services.encryption_service import EncryptionService
        import app.services.encryption_service as enc_mod
        enc_mod._instance = EncryptionService(app.config["ENCRYPTION_KEY"])

    app.extensions["mongo_client"] = mongo_client
    app.extensions["db"] = db
    app.extensions["w3"] = w3


def get_db():
    """Get the MongoDB database instance."""
    return db


def get_web3():
    """Get the Web3 instance."""
    return w3
