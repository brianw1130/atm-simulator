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
    peppered = f"{pepper}{pin}".encode("utf-8")
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
    peppered = f"{pepper}{pin}".encode("utf-8")
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
_COMMON_PINS: frozenset[str] = frozenset({
    "0000", "1234", "4321", "1111", "2222", "3333",
    "4444", "5555", "6666", "7777", "8888", "9999",
    "0123", "9876", "1357", "2468",
})


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
