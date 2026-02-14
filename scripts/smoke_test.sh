#!/usr/bin/env bash
# Smoke test script for deployed ATM simulator
# Usage: ./scripts/smoke_test.sh <BASE_URL>
# Example: ./scripts/smoke_test.sh http://1.2.3.4:8000

set -euo pipefail

BASE_URL="${1:?Usage: $0 <BASE_URL>}"
BASE_URL="${BASE_URL%/}"  # Remove trailing slash

PASS=0
FAIL=0

green() { printf "\033[32m%s\033[0m\n" "$1"; }
red() { printf "\033[31m%s\033[0m\n" "$1"; }
bold() { printf "\033[1m%s\033[0m\n" "$1"; }

check() {
  local name="$1"
  local expected_code="$2"
  local actual_code="$3"

  if [ "$actual_code" = "$expected_code" ]; then
    green "  PASS: ${name} (HTTP ${actual_code})"
    PASS=$((PASS + 1))
  else
    red "  FAIL: ${name} (expected HTTP ${expected_code}, got HTTP ${actual_code})"
    FAIL=$((FAIL + 1))
  fi
}

bold "ATM Simulator Smoke Tests"
bold "Target: ${BASE_URL}"
echo ""

# Test 1: Health endpoint
bold "[1/4] Health Check"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
check "GET /health" "200" "${HTTP_CODE}"

# Test 2: Readiness endpoint
bold "[2/4] Readiness Check"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/ready")
check "GET /ready" "200" "${HTTP_CODE}"

# Test 3: Auth login
bold "[3/4] Auth Login"
LOGIN_BODY=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"card_number": "1000-0001-0001", "pin": "1234"}')
SESSION_ID=$(echo "${LOGIN_BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
if [ -n "${SESSION_ID}" ]; then
  check "POST /api/v1/auth/login" "200" "200"
else
  check "POST /api/v1/auth/login" "200" "401"
fi

# Test 4: Balance inquiry (requires session from login)
bold "[4/4] Balance Inquiry"
if [ -n "${SESSION_ID}" ]; then
  # Get account list to find account ID, then check balance
  ACCOUNTS_BODY=$(curl -s "${BASE_URL}/api/v1/accounts/" -H "X-Session-ID: ${SESSION_ID}")
  ACCOUNT_ID=$(echo "${ACCOUNTS_BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin)['accounts'][0]['id'])" 2>/dev/null || echo "")
  if [ -n "${ACCOUNT_ID}" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      "${BASE_URL}/api/v1/accounts/${ACCOUNT_ID}/balance" \
      -H "X-Session-ID: ${SESSION_ID}")
    check "GET /api/v1/accounts/{id}/balance" "200" "${HTTP_CODE}"
  else
    red "  SKIP: Could not extract account ID from accounts response"
    FAIL=$((FAIL + 1))
  fi
else
  red "  SKIP: Could not extract session_id from login response"
  FAIL=$((FAIL + 1))
fi

# Summary
echo ""
bold "Results: ${PASS} passed, ${FAIL} failed"

if [ "${FAIL}" -gt 0 ]; then
  red "SMOKE TESTS FAILED"
  exit 1
fi

green "ALL SMOKE TESTS PASSED"
exit 0
