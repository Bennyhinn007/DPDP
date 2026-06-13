"""
Application Configuration.

Environment-specific settings for development, testing, and production.
"""

import os
from datetime import timedelta


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    JSON_SORT_KEYS = False

    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "dpdp_healthcare_db")

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = "HS256"  # RS256 in production with key pair

    # Blockchain (Ganache)
    GANACHE_URL = os.environ.get("GANACHE_URL", "http://localhost:8545")
    GANACHE_CHAIN_ID = int(os.environ.get("GANACHE_CHAIN_ID", "1337"))

    # Encryption
    ENCRYPTION_KEY_STORE_PATH = os.environ.get("KEY_STORE_PATH", "./keystore")
    AES_KEY_ROTATION_DAYS = 90

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Rate Limiting
    RATE_LIMIT_PATIENT = 100  # requests per minute
    RATE_LIMIT_DOCTOR = 200
    RATE_LIMIT_PHARMACY = 200
    RATE_LIMIT_ADMIN = 300
    RATE_LIMIT_DPO = 300

    # Session
    SESSION_IDLE_TIMEOUT_PATIENT = timedelta(minutes=30)
    SESSION_IDLE_TIMEOUT_CLINICAL = timedelta(minutes=15)
    MAX_CONCURRENT_SESSIONS_PATIENT = 3
    MAX_CONCURRENT_SESSIONS_DOCTOR = 2
    MAX_CONCURRENT_SESSIONS_ADMIN = 1

    # Security
    BCRYPT_COST_FACTOR = 12
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)

    # Blockchain Anchoring
    BLOCKCHAIN_ANCHOR_TIMEOUT = 10  # seconds


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    MONGO_DB_NAME = "dpdp_healthcare_dev"
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "ALqZ-f2S9tSruxC8YlTTInzGCYgFkTFztlerw8nxsyk=")


class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    DEBUG = False
    TESTING = True
    MONGO_DB_NAME = "dpdp_healthcare_test"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    BCRYPT_COST_FACTOR = 4  # Faster hashing for tests
    ENCRYPTION_KEY = "ALqZ-f2S9tSruxC8YlTTInzGCYgFkTFztlerw8nxsyk="  # Stable test key


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    JWT_ALGORITHM = "RS256"
    BCRYPT_COST_FACTOR = 12


_config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(config_name: str = "development"):
    """Get configuration class by environment name."""
    return _config_map.get(config_name, DevelopmentConfig)
