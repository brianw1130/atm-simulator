"""Security utilities for PIN hashing, input sanitization, and session management.

Owner: Security Engineer
Coverage requirement: 100%

This module provides cryptographic operations for the ATM simulator.
All PIN-related functions follow security best practices:
- PINs are never logged, even in masked form.
- bcrypt with application-level pepper is used for PIN hashing.
- Session tokens use cryptographically secure random generation.

Functions:
    hash_pin: Hash a PIN using bcrypt with pepper.
    verify_pin: Verify a PIN against its bcrypt hash.
    generate_session_token: Generate a cryptographically secure session token.
    generate_reference_number: Generate a unique transaction reference number.
    validate_pin_complexity: Enforce PIN complexity rules.
    sanitize_input: Strip and sanitize user input.

Security Review — 2026-02-12
=============================
Reviewer: Security Engineer agent

Scope reviewed:
    - src/atm/utils/security.py — PIN hashing, session tokens, input sanitization
    - src/atm/utils/formatting.py — Account number masking
    - src/atm/services/auth_service.py — Authentication, sessions, lockout, PIN change
    - src/atm/services/audit_service.py — Audit logging
    - src/atm/services/transaction_service.py — Withdrawal, deposit, transfer
    - src/atm/services/account_service.py — Balance inquiry
    - src/atm/services/statement_service.py — PDF statement generation
    - src/atm/api/ (all routers) — Input validation, error handling, authorization
    - src/atm/schemas/ (all schemas) — Pydantic validation rules
    - src/atm/models/ (all models) — Data integrity, PIN storage
    - src/atm/db/seed.py — Seed data handling
    - src/atm/config.py — Configuration and secrets
    - src/atm/main.py — App factory

Issues found and fixed:
    1. [CRITICAL] IDOR vulnerability in GET /accounts/{account_id}/balance.
       The endpoint accepted any account_id without verifying ownership by the
       authenticated customer. An authenticated user could view any other
       customer's balance and transaction history by guessing integer IDs.
       FIX: Added ownership check in src/atm/api/accounts.py — the endpoint
       now loads the customer's accounts and verifies the requested account_id
       belongs to them before proceeding. Returns 403 Forbidden on mismatch.

Issues noted but acceptable (low risk / by design):
    1. Audit logs store unmasked account numbers in the details JSON
       (transaction_service.py lines 472-473). This is appropriate for
       compliance and investigation purposes. Audit log data is not exposed
       through any API endpoint, so this is acceptable.
    2. Timing side-channel on card existence: when a card_number is not found,
       the auth flow returns immediately without performing a bcrypt check,
       making it theoretically faster than an invalid-PIN response. Both
       return the same generic "Authentication failed" message. Risk is low
       for an ATM simulator; in production, a dummy bcrypt.checkpw call
       should be added to equalize response timing.
    3. The Account model has a masked_account_number property using "X" as
       the mask character, while formatting.py uses "*". This inconsistency
       is cosmetic — the model property is not used in any API response
       (formatting.py's mask_account_number is used instead). No fix needed.
    4. Default config values for secret_key and pin_pepper are
       "change-me-in-production". These are appropriate for development but
       must be overridden in production via environment variables.
    5. SQL echo is enabled when environment=development (db/session.py).
       This could log query parameters in dev. Acceptable for development;
       must be disabled in production (which it is, since echo is tied to
       is_development).

Verified secure (no issues found):
    - PIN hashing: bcrypt with rounds=12 and application-level pepper. Correct.
    - PINs never logged: grep across entire src/ confirms no log/print
      statements contain PIN values. Audit log details use reason codes only.
    - Error messages: Authentication failures return generic "Authentication
      failed" for both invalid card and invalid PIN. No card existence leak.
    - Session tokens: Generated via secrets.token_urlsafe(32). Correct.
    - Session expiry: 2-minute inactivity timeout enforced in validate_session.
    - Session invalidation: logout removes session from in-memory store.
    - Input validation: All API endpoints use Pydantic schemas with field
      validators (digits-only for PINs, gt=0 for amounts, pattern for
      deposit_type, etc.). Validation happens before business logic.
    - No raw SQL: All database queries use SQLAlchemy ORM with parameterized
      queries. No text() or raw SQL strings found.
    - Account numbers masked: All user-facing responses use
      mask_account_number() from formatting.py.
    - Audit coverage: All auth events (success, failure, lockout), all
      transaction events (success, declined), PIN changes (success, failure),
      balance inquiries, and statement generation are logged.
    - PIN complexity: Validates length (4-6 digits), rejects repeated digits,
      sequential sequences, and common PINs via blocklist.
    - Account lockout: 3 failed attempts triggers 30-minute lockout.
    - Daily limits: Withdrawal ($500) and transfer ($2,500) limits enforced.
    - No stack traces in error responses: All exceptions caught and converted
      to HTTPException with safe detail messages.
    - sanitize_input: Strips whitespace, removes null bytes, escapes HTML.

Overall security posture: GOOD.
    The codebase follows security best practices for a financial application
    simulator. The one critical IDOR vulnerability has been fixed. The
    remaining noted items are low-risk or by-design decisions. The application
    is ready for Sprint 4 gate from a security perspective.
"""

import html
import secrets
import time

import bcrypt


def hash_pin(pin: str, pepper: str) -> str:
    """Hash a PIN using bcrypt with an application-level pepper.

    Prepends the pepper to the PIN before hashing to add a layer of
    defense beyond the per-hash salt that bcrypt provides.

    Args:
        pin: The plaintext PIN to hash. Must be a digit string.
        pepper: The application-level secret pepper value.

    Returns:
        The bcrypt hash as a UTF-8 string.

    Raises:
        ValueError: If pin or pepper is empty.
    """
    if not pin:
        raise ValueError("PIN must not be empty")
    if not pepper:
        raise ValueError("Pepper must not be empty")
    peppered = f"{pepper}{pin}".encode()
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(peppered, salt)
    return hashed.decode("utf-8")


def verify_pin(pin: str, pin_hash: str, pepper: str) -> bool:
    """Verify a PIN against its bcrypt hash using the application pepper.

    Args:
        pin: The plaintext PIN to verify.
        pin_hash: The stored bcrypt hash string.
        pepper: The application-level secret pepper value.

    Returns:
        True if the PIN matches the hash, False otherwise.
    """
    if not pin or not pin_hash or not pepper:
        return False
    peppered = f"{pepper}{pin}".encode()
    try:
        return bcrypt.checkpw(peppered, pin_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def generate_session_token() -> str:
    """Generate a cryptographically secure session token.

    Uses ``secrets.token_urlsafe`` with 32 bytes of randomness,
    producing a 43-character URL-safe base64 string.

    Returns:
        A URL-safe random token string.
    """
    return secrets.token_urlsafe(32)


def generate_reference_number() -> str:
    """Generate a unique transaction reference number.

    Format: ``REF-{timestamp_hex}-{random_hex}`` where timestamp_hex is
    the current Unix timestamp in hexadecimal and random_hex is 4 bytes
    of cryptographically secure random data in hexadecimal.

    Returns:
        A reference number string, e.g. ``REF-65a1b2c3-f4e5d6c7``.
    """
    timestamp_hex = format(int(time.time()), "x")
    random_hex = secrets.token_hex(4)
    return f"REF-{timestamp_hex}-{random_hex}"


# PINs that are statistically common or trivially guessable.
_COMMON_PINS: frozenset[str] = frozenset(
    {
        "0000",
        "1234",
        "4321",
        "1111",
        "2222",
        "3333",
        "4444",
        "5555",
        "6666",
        "7777",
        "8888",
        "9999",
        "0123",
        "9876",
        "1357",
        "2468",
    }
)


def validate_pin_complexity(pin: str) -> tuple[bool, str]:
    """Validate that a PIN meets complexity requirements.

    Rules enforced:
        1. Must be 4-6 digits only.
        2. Must not be all the same digit (e.g. 1111, 000000).
        3. Must not be a sequential ascending sequence (e.g. 1234, 123456).
        4. Must not be a sequential descending sequence (e.g. 4321, 654321).
        5. Must not appear in the common PINs blocklist.

    Args:
        pin: The PIN string to validate.

    Returns:
        A tuple of (is_valid, reason). If valid, reason is an empty string.
        If invalid, reason describes why the PIN was rejected.
    """
    if not pin or not pin.isdigit():
        return False, "PIN must contain only digits"

    if len(pin) < 4 or len(pin) > 6:
        return False, "PIN must be 4-6 digits long"

    if len(set(pin)) == 1:
        return False, "PIN must not be all the same digit"

    digits = [int(d) for d in pin]
    is_ascending = all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1))
    if is_ascending:
        return False, "PIN must not be a sequential ascending sequence"

    is_descending = all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1))
    if is_descending:
        return False, "PIN must not be a sequential descending sequence"

    if pin in _COMMON_PINS:
        return False, "PIN is too common and easily guessable"

    return True, ""


def sanitize_input(value: str) -> str:
    """Sanitize user input by stripping whitespace, removing null bytes, and escaping HTML.

    This function provides defense-in-depth input sanitization. Primary
    validation should be handled by Pydantic schemas at the API boundary;
    this function adds an additional layer of protection.

    Args:
        value: The raw input string to sanitize.

    Returns:
        The sanitized string with whitespace stripped, null bytes removed,
        and HTML special characters escaped.
    """
    cleaned = value.strip()
    cleaned = cleaned.replace("\x00", "")
    cleaned = html.escape(cleaned, quote=True)
    return cleaned
