"""Seed the database with sample data for development.

Usage:
    python -m scripts.seed_db

Creates the test accounts defined in CLAUDE.md:
    - Alice Johnson: Checking ($5,250) + Savings ($12,500), PIN 1234
    - Bob Williams: Checking ($850.75), PIN 5678
    - Charlie Davis: Checking ($0) + Savings ($100), PIN 9012
"""

# TODO: Implement database seeding
# This script should:
# 1. Import async engine and session from src.atm.db.session
# 2. Create customers, accounts, and cards using the models
# 3. Hash PINs using src.atm.utils.security.hash_pin()
# 4. Be idempotent (safe to run multiple times)

if __name__ == "__main__":
    print("TODO: Implement database seeding")
