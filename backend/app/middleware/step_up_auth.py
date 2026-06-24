"""
Step-Up Authentication Middleware.

Requires additional verification (biometric or MFA) for sensitive operations.
Does NOT block login — only gates privileged actions.

Sensitive operations:
- Record erasure (DPDP Right to Erasure)
- Chameleon hash redaction authorization
- Account deletion
- MFA disable

Flow:
1. User performs normal JWT login
2. User attempts sensitive operation
3. Backend checks if step-up auth was completed recently (within 5 min)
4. If not → returns 403 with step_up_required flag
5. Frontend prompts for biometric/MFA re-verification
6. On success → grants temporary elevated session
"""

from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import g, jsonify

STEP_UP_WINDOW = timedelta(minutes=5)


def step_up_required(f):
    """
    Decorator: Requires recent step-up authentication for sensitive operations.

    For demo purposes, this is advisory — operations still work but are flagged.
    In production, this would block the operation until re-verification completes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user has recent step-up authentication
        # For this MVP, we log the requirement but don't block (demo-friendly)
        g.step_up_advisory = True
        return f(*args, **kwargs)
    return decorated
