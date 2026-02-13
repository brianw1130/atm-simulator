# User Guide

> **Owner:** UX Designer

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (recommended), or
- **Python 3.12+** with pip for local development

### Running with Docker

```bash
# Clone the repository
git clone https://github.com/brianw/atm-simulator.git
cd atm-simulator

# Start all services (app, PostgreSQL, Redis)
docker-compose up -d

# The API is available at http://localhost:8000
# API docs at http://localhost:8000/docs (development mode only)
```

### Running Locally (without Docker)

```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment variables (or create a .env file from .env.example)
export DATABASE_URL="sqlite+aiosqlite:///./atm.db"
export DATABASE_URL_SYNC="sqlite:///./atm.db"
export SECRET_KEY="dev-secret-key"
export PIN_PEPPER="dev-pepper"
export ENVIRONMENT="development"

# Seed the database with test data
python3 scripts/seed_db.py

# Start the API server
uvicorn src.atm.main:app --reload --port 8000
```

### First Login

Use one of the test accounts listed in [Test Accounts](#test-accounts) below. For example, to log in as Alice:

- **Card number:** `1000-0001-0001`
- **PIN:** `1234`

---

## Web UI (v2.0)

The ATM Simulator includes a skeuomorphic web interface that renders a realistic ATM kiosk in the browser. Open `http://localhost:8000` after starting the application.

### Using the Web ATM

1. **Insert Card** -- Type a card number (e.g., `1000-0001-0001`) using the on-screen keypad or your physical keyboard, then press Enter.

2. **Enter PIN** -- Type your 4-6 digit PIN. Input is masked. Press Enter to authenticate or Cancel to return.

3. **Main Menu** -- Use the side buttons to navigate:
   - **Left buttons:** Balance Inquiry, Withdraw Cash, Deposit, Transfer Funds
   - **Right buttons:** Account Statement, Change PIN, -, Logout

4. **Transactions** -- Follow on-screen prompts. Withdrawal amounts can be selected via quick-select side buttons ($20-$200) or entered via the keypad. Transfers and deposits use the keypad for amount entry.

5. **Receipts** -- After completing a transaction, the receipt printer animates and you can choose "Another Transaction" or "Done" (logout).

### Keyboard Shortcuts

The physical keyboard maps to the ATM keypad:

| Key | ATM Function |
|---|---|
| `0-9` | Numeric keypad digits |
| `Enter` | Enter / Confirm |
| `Backspace` | Clear / Correct |
| `Escape` | Cancel / Back |

### Session Timeout

After 2 minutes of inactivity, a 30-second countdown warning appears. Press any key to reset the timer. If the countdown reaches zero, the session expires and the ATM returns to the welcome screen.

---

## Terminal UI

The ATM simulator includes a terminal-based user interface built with [Textual](https://textual.textualize.io/).

### Launching the Terminal UI

```bash
python3 -m src.atm.ui.app
```

> **Note:** The API server must be running at `http://localhost:8000` before launching the UI.

### Screen Navigation

The terminal UI follows a typical ATM interaction flow:

1. **Welcome Screen** -- Enter your card number (e.g., `1000-0001-0001`) and press Enter or click "Insert Card".

2. **PIN Entry** -- Enter your 4-6 digit PIN. The input is masked. Press Enter or click "Enter" to authenticate. Click "Cancel" to return to the welcome screen.

3. **Main Menu** -- After successful login, the main menu displays:
   - Your name and account information
   - **Balance Inquiry** -- View current balance and last 5 transactions
   - **Withdraw Cash** -- Quick-select ($20, $40, $60, $100, $200) or custom amount
   - **Deposit** -- Cash or check deposit with amount entry
   - **Transfer Funds** -- Transfer between your accounts or to another account
   - **Account Statement** -- Generate a PDF statement for a date range
   - **Change PIN** -- Instructions for PIN change via the API
   - **Logout** -- End your session and return to the welcome screen

4. **Operation Screens** -- Each operation screen has a "Back to Menu" button to return to the main menu.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit the current form |
| `q` | Quit the application |
| `Tab` | Move between fields |

---

## API Usage

All API endpoints are prefixed with `/api/v1/`. Include the `X-Session-ID` header (returned by login) in all authenticated requests.

### Authentication

**Login:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"card_number": "1000-0001-0001", "pin": "1234"}'
```

Response:

```json
{
  "session_id": "abc123...",
  "account_number": "1000-0001-0001",
  "customer_name": "Alice Johnson",
  "message": "Authentication successful"
}
```

Save the `session_id` for subsequent requests.

**Logout:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "X-Session-ID: <your-session-id>"
```

### Balance Inquiry

```bash
curl http://localhost:8000/api/v1/accounts/1/balance \
  -H "X-Session-ID: <your-session-id>"
```

### Cash Withdrawal

Amounts must be multiples of $20. Amount is in cents.

```bash
curl -X POST http://localhost:8000/api/v1/transactions/withdraw \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"amount_cents": 10000}'
```

### Cash or Check Deposit

```bash
# Cash deposit
curl -X POST http://localhost:8000/api/v1/transactions/deposit \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"amount_cents": 50000, "deposit_type": "cash"}'

# Check deposit
curl -X POST http://localhost:8000/api/v1/transactions/deposit \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"amount_cents": 100000, "deposit_type": "check", "check_number": "4521"}'
```

### Fund Transfer

```bash
curl -X POST http://localhost:8000/api/v1/transactions/transfer \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"amount_cents": 25000, "to_account_number": "1000-0001-0002"}'
```

### Account Statement

```bash
# Generate a 7-day statement
curl -X POST http://localhost:8000/api/v1/statements/generate \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"days": 7}'

# Custom date range
curl -X POST http://localhost:8000/api/v1/statements/generate \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"start_date": "2026-01-01", "end_date": "2026-01-31"}'
```

### PIN Change

```bash
curl -X POST http://localhost:8000/api/v1/auth/pin/change \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your-session-id>" \
  -d '{"current_pin": "1234", "new_pin": "5678", "confirm_pin": "5678"}'
```

PIN rules:
- Must be 4-6 digits
- Cannot be all the same digit (e.g., 1111)
- Cannot be sequential (e.g., 1234, 4321)

### Health Checks

```bash
# Liveness probe (always 200)
curl http://localhost:8000/health

# Readiness probe (checks DB + Redis)
curl http://localhost:8000/ready
```

---

## Admin Panel

The admin panel provides account management and monitoring capabilities.

### Accessing the Admin Panel

Navigate to `http://localhost:8000/admin/login` in a web browser.

Default admin credentials are created by the database seeder (`scripts/seed_db.py`).

### Dashboard Features

- **Account Management** -- View all accounts with customer names, balances, and status. Freeze or unfreeze individual accounts.
- **Audit Logs** -- View all security-relevant events (logins, transactions, admin actions). Filter by event type.
- **Maintenance Mode** -- Enable or disable ATM maintenance mode. When enabled, all customer API endpoints return 503 Service Unavailable while admin and health endpoints remain accessible.

### Admin API Endpoints

All admin API endpoints require an authenticated admin session cookie.

```bash
# Get maintenance status
curl http://localhost:8000/admin/api/maintenance/status \
  -b "admin_session=<token>"

# Enable maintenance mode
curl -X POST http://localhost:8000/admin/api/maintenance/enable \
  -H "Content-Type: application/json" \
  -b "admin_session=<token>" \
  -d '{"reason": "Scheduled maintenance"}'

# Disable maintenance mode
curl -X POST http://localhost:8000/admin/api/maintenance/disable \
  -b "admin_session=<token>"
```

---

## Test Accounts

| Customer | Account | Type | Balance | PIN |
|---|---|---|---|---|
| Alice Johnson | 1000-0001-0001 | Checking | $5,250.00 | 1234 |
| Alice Johnson | 1000-0001-0002 | Savings | $12,500.00 | 1234 |
| Bob Williams | 1000-0002-0001 | Checking | $850.75 | 5678 |
| Charlie Davis | 1000-0003-0001 | Checking | $0.00 | 9012 |
| Charlie Davis | 1000-0003-0002 | Savings | $100.00 | 9012 |
