# Frontend Architecture

> **Owner:** Software Engineer (Frontend/UX)

## Overview

The ATM Simulator web UI is a skeuomorphic, single-page application built with React 18 + TypeScript (strict mode). It renders a realistic ATM kiosk in the browser — complete with a metallic housing, physical keypad, card slot, cash dispenser, and CRT-style screen — and communicates with the FastAPI backend via REST.

**Key design principles:**

- **State machine, not router.** ATMs don't have URL bars. A `useReducer` state machine drives all 17 screens through a deterministic, linear flow.
- **GPU-composited animations only.** All animations use `transform` and `opacity` (Framer Motion). No layout-triggering properties.
- **Accessibility first.** `prefers-reduced-motion` disables all animations. Every interactive element has `aria-label`. Physical keyboard mapping (0-9, Enter, Escape, Backspace) mirrors the on-screen keypad.
- **No external state libraries.** React Context + `useReducer` is sufficient for a linear ATM flow.

## Technology Stack

| Technology | Version | Purpose |
|---|---|---|
| React | 18.3 | Component framework |
| TypeScript | 5.6+ | Strict type safety (`strict: true`, `noUncheckedIndexedAccess`) |
| Vite | 6.0 | Build tool and dev server |
| Framer Motion | 11.15 | Spring physics animations, `AnimatePresence` screen transitions |
| Axios | 1.7 | HTTP client with request/response interceptors |
| Vitest | 2.1 | Unit and component testing |
| React Testing Library | 16.x | Component test utilities |
| Playwright | 1.58 | Browser E2E testing |

## State Machine

The application state is managed by a single `useReducer` state machine in `state/atmReducer.ts`. There is no React Router — screen transitions are state changes.

### Screens (17 total)

```
welcome → pin_entry → main_menu ─┬→ balance_inquiry
                                  ├→ withdrawal → withdrawal_confirm → withdrawal_receipt
                                  ├→ deposit (type select → amount entry) → deposit_receipt
                                  ├→ transfer → transfer_confirm → transfer_receipt
                                  ├→ statement
                                  ├→ pin_change
                                  └→ (logout → welcome)

Special screens: session_timeout, error, maintenance
```

### Actions (16 types)

| Action | Trigger | Effect |
|---|---|---|
| `INSERT_CARD` | Card number submitted on welcome | Transition to `pin_entry` |
| `LOGIN_SUCCESS` | PIN verified by API | Store session, accounts; go to `main_menu` |
| `LOGIN_FAILURE` | API rejects PIN | Set error message |
| `NAVIGATE` | Side button or menu selection | Push current screen to history, go to target |
| `GO_BACK` | Back/Cancel button | Pop from screen history |
| `SELECT_ACCOUNT` | Account side button on balance screen | Update `selectedAccountId` |
| `SET_ACCOUNTS` | Account list refreshed | Update `accounts` array |
| `STAGE_TRANSACTION` | Amount entered or deposit type selected | Store pending transaction, go to confirm screen |
| `TRANSACTION_SUCCESS` | API confirms transaction | Store receipt, go to receipt screen |
| `TRANSACTION_FAILURE` | API rejects transaction | Set error, clear pending transaction |
| `SET_LOADING` | API call starts/completes | Toggle loading spinner |
| `SESSION_TIMEOUT` | Idle timer expires | Reset state, go to `session_timeout` |
| `MAINTENANCE_MODE` | 503 from API interceptor | Go to `maintenance` screen |
| `LOGOUT` | User clicks Done/Logout | Reset to `INITIAL_ATM_STATE` |
| `CLEAR_ERROR` | Error dismissed | Clear `lastError` |
| `REFRESH_SESSION_TIMER` | User activity detected | Reset `sessionExpiresAt` |

### State Shape

```typescript
interface ATMState {
  currentScreen: ATMScreen;       // Which of 17 screens is active
  screenHistory: ATMScreen[];     // Back-button stack
  sessionId: string | null;       // Server session token
  customerName: string | null;    // Display name after login
  accountNumber: string | null;   // Primary account number
  cardNumber: string | null;      // Card used for login
  accounts: AccountSummary[];     // All accounts for this customer
  selectedAccountId: number | null; // Active account for operations
  lastError: string | null;       // Error message to display
  isLoading: boolean;             // API call in progress
  pendingTransaction: PendingTransaction | null; // Staged for confirmation
  lastReceipt: TransactionReceipt | null; // Completed transaction receipt
  sessionExpiresAt: number | null; // Idle timer expiration timestamp
}
```

## Component Architecture

### Hierarchy

```
App
├── ATMFrame                     (metallic housing, gradient background)
│   ├── SideButtons (left)       (4 context-sensitive buttons)
│   ├── ScreenBezel              (CRT glow, scanline effect)
│   │   ├── AnimatePresence      (screen transition orchestration)
│   │   │   └── [ActiveScreen]   (one of 17 screen components)
│   │   └── IdleWarningOverlay   (30s countdown before timeout)
│   ├── SideButtons (right)      (4 context-sensitive buttons)
│   ├── ReceiptPrinter           (animated receipt paper)
│   ├── CardSlot                 (card insertion animation)
│   ├── NumericKeypad            (0-9, Enter, Clear, Cancel)
│   └── CashDispenser            (bill dispensing animation)
```

### Component Categories

**ATM Housing** (`components/atm-housing/`):
- `ATMFrame` — Outer metallic frame with gradient and rounded corners
- `ScreenBezel` — CRT-style screen with green glow, scanlines, and `screen-display` class
- `SideButtons` — 4 buttons per side, context-sensitive labels driven by `App.tsx`
- `NumericKeypad` — 12-button grid (0-9, Enter, Clear, Cancel) with press feedback
- `CardSlot` — Animated card insertion/ejection
- `CashDispenser` — Bill dispensing with staggered animation, flap element
- `ReceiptPrinter` — Receipt paper sliding out animation

**Screens** (`components/screens/`):
Each screen is a self-contained component that reads state via `useATMContext()` and dispatches actions. Screens that accept keypad input expose static `keypadHandlers` for `App.tsx` to wire.

**Shared** (`components/shared/`):
Reusable display components (loading spinners, formatted amounts).

### Side Button Wiring

Side buttons are context-sensitive — their labels and actions change per screen. `App.tsx` builds the button configuration in `buildSideButtons(side)` based on `state.currentScreen`:

- **Main menu**: Balance, Withdraw, Deposit, Transfer (left); Statement, PIN Change, -, Logout (right)
- **Withdrawal**: Quick amounts $20-$200 (left); -, -, -, Back (right)
- **Receipt screens**: -, -, Another Transaction, Done (right)

### Keypad Wiring

The `NumericKeypad` component fires generic events (`onDigit`, `onClear`, `onCancel`, `onEnter`). `App.tsx` routes these to the active screen's static `keypadHandlers` object based on `currentScreen`. This decouples the keypad UI from screen-specific logic.

Physical keyboard events are also captured:
- `0-9` → `onDigit`
- `Enter` → `onEnter`
- `Backspace` → `onClear`
- `Escape` → `onCancel`

## API Integration

### Client (`api/client.ts`)

A configured Axios instance with two interceptors:

1. **Request interceptor**: Attaches `X-Session-ID` header from `sessionStorage` to every request.
2. **Response interceptor**: Dispatches custom DOM events on error responses:
   - `401` → `atm:session-expired` event → triggers `SESSION_TIMEOUT` action
   - `503` → `atm:maintenance` event → triggers `MAINTENANCE_MODE` action

### Endpoint Functions (`api/endpoints.ts`)

Typed wrapper functions for each API call:
- `login(cardNumber, pin)` → `POST /auth/login`
- `logout()` → `POST /auth/logout`
- `getBalance(accountId)` → `GET /accounts/{id}/balance`
- `withdraw(amountCents)` → `POST /transactions/withdraw`
- `deposit(amountCents, depositType, checkNumber?)` → `POST /transactions/deposit`
- `transfer(destAccount, amountCents)` → `POST /transactions/transfer`
- `generateStatement(days)` → `POST /statements/generate`
- `downloadStatement(filename)` → `GET /statements/download/{filename}`
- `changePin(currentPin, newPin, confirmPin)` → `POST /auth/pin/change`
- `refreshSession()` → `POST /session/refresh`
- `getAccounts()` → `GET /accounts`

### Session Management

Session tokens are stored in `sessionStorage` (cleared on tab close). The `useIdleTimer` hook manages the 2-minute inactivity timeout:

1. Monitors `mousedown`, `keydown`, `touchstart` events
2. Resets a 2-minute timer on activity (throttled to 1 reset/second)
3. Shows a 30-second countdown warning overlay before expiration
4. Periodically calls `POST /session/refresh` every 60 seconds to keep the server-side session alive
5. Dispatches `SESSION_TIMEOUT` when the timer expires

## Animation System

### Screen Transitions

All screen transitions use Framer Motion's `AnimatePresence` with `mode="wait"`:

```typescript
const screenVariants = {
  enter: { opacity: 0, y: 20 },
  center: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
};
```

### Hardware Animations

- **Card insertion**: CSS transform slide-in when `isCardInserted` becomes true
- **Cash dispensing**: Staggered bill emergence with Framer Motion `staggerChildren`
- **Receipt printing**: Paper slide-up animation when `isReceiptPrinting` is true
- **Keypad press**: Scale-down transform on button activation

### Accessibility

When `prefers-reduced-motion` is enabled:
- `useReducedMotion()` hook returns `true`
- Screen transitions use `screenVariantsReduced` (instant, no motion)
- Overlay animations are disabled
- Countdown pulse effect is suppressed
- All functionality remains identical — only motion is removed

## CSS Architecture

### Design Approach

Plain CSS with CSS custom properties (variables). No CSS-in-JS.

### Key Visual Effects

- **Metallic housing**: Linear gradient (`#a8a8a8` → `#d4d4d4` → `#a8a8a8`) with inner shadow
- **CRT screen glow**: Green `box-shadow` on `.screen-display` (`0 0 30px rgba(0,255,0,0.15)`)
- **Scanline overlay**: Repeating linear gradient producing horizontal lines
- **Keypad buttons**: Raised appearance with `box-shadow`, depressed state on `:active`
- **Side buttons**: Arrow-shaped indicators connecting buttons to screen edge

### Responsive Strategy

The ATM is designed for desktop and tablet (fixed aspect ratio). CSS `scale()` transform with `min()` scales the entire ATM housing to fit smaller viewports while maintaining proportions.

## Build and Deployment

### Development

```bash
cd frontend
npm install
npm run dev          # Vite dev server at :5173, proxies /api to :8000
```

### Production

The Dockerfile uses a multi-stage build:
1. **Node.js stage**: `npm ci && npm run build` → produces `frontend/dist/`
2. **Python stage**: Copies `frontend/dist/` into the image
3. **FastAPI serves static files**: `_mount_frontend()` in `main.py` mounts `/assets` and serves `index.html` for all non-API routes

### Docker Compose (Development)

```yaml
frontend:
  image: node:20-alpine
  command: sh -c "npm install && npm run dev -- --host 0.0.0.0"
  ports: ["5173:5173"]
```

In development, the Vite dev server runs separately and proxies API calls to the backend.

## Testing Strategy

### Unit / Component Tests (Vitest)

- **State machine**: All 16 action types tested, including edge cases
- **API client**: Interceptor behavior (session header attachment, 401/503 handling)
- **Endpoint functions**: Mocked Axios responses for all API calls
- **Hooks**: `useATMContext` (error boundary), `useIdleTimer` (timer logic)
- **Housing components**: Rendering, click handlers, keyboard event mapping
- **Screen components**: Rendering per state, dispatch verification, side button wiring

### Browser E2E Tests (Playwright)

Playwright tests run against a live Vite dev server + backend:
- Login flow (card → PIN → main menu)
- Navigation between screens via side buttons
- Balance inquiry, withdrawal, deposit, transfer flows
- PIN change flow
- Error and edge cases (clear button, Escape key, multiple navigations)
- Animation elements (card slot, cash dispenser, CRT glow)

### Coverage Thresholds

Enforced in `vite.config.ts`:

| Metric | Threshold |
|---|---|
| Lines | 90% |
| Statements | 90% |
| Branches | 85% |
| Functions | 48% (v8 inflates denominator for React components) |
