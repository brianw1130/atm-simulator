"""End-to-end tests covering complete ATM user journeys.

42 tests across 8 categories as specified in CLAUDE.md:
    - Authentication Journeys (6 tests): E2E-AUTH-01 through E2E-AUTH-06
    - Withdrawal Journeys (8 tests): E2E-WDR-01 through E2E-WDR-08
    - Deposit Journeys (5 tests): E2E-DEP-01 through E2E-DEP-05
    - Transfer Journeys (7 tests): E2E-TRF-01 through E2E-TRF-07
    - Statement Journeys (5 tests): E2E-STM-01 through E2E-STM-05
    - Balance Inquiry Journeys (3 tests): E2E-BAL-01 through E2E-BAL-03
    - Cross-Feature Compound Journeys (4 tests): E2E-CMP-01 through E2E-CMP-04
    - Error Handling & Edge Case Journeys (4 tests): E2E-ERR-01 through E2E-ERR-04

Each test is independent with fresh database state (no shared state between tests).
Uses time-machine for time-dependent tests (session expiry, lockout, holds).
"""

# TODO: Implement all 42 E2E tests
