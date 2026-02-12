"""Main menu screen after successful authentication.

Owner: UX Designer
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import httpx
from textual.screen import Screen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.atm.ui.app import ATMApp


class MainMenuScreen(Screen[None]):
    """Main menu screen displaying account info and operation buttons."""

    def compose(self) -> ComposeResult:
        """Compose the main menu layout."""
        with Static(classes="menu-container"):
            yield Static("", id="greeting", classes="title")
            yield Static("", id="account-info", classes="info-message")
            yield Button("Balance Inquiry", variant="primary", id="balance-btn")
            yield Button("Withdraw Cash", variant="primary", id="withdraw-btn")
            yield Button("Deposit", variant="primary", id="deposit-btn")
            yield Button("Transfer Funds", variant="primary", id="transfer-btn")
            yield Button("Account Statement", variant="primary", id="statement-btn")
            yield Button("Change PIN", variant="warning", id="change-pin-btn")
            yield Button("Logout", variant="error", id="logout-btn")
            yield Static("", id="menu-message", classes="info-message")

    def on_mount(self) -> None:
        """Display customer name and account info."""
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        greeting = self.query_one("#greeting", Static)
        greeting.update(f"Welcome, {atm_app.customer_name}")

        account_info = self.query_one("#account-info", Static)
        if atm_app.accounts:
            lines = []
            for acct in atm_app.accounts:
                acct_type = acct.get("account_type", "")
                acct_num = acct.get("account_number", "")
                balance = acct.get("available_balance", acct.get("balance", ""))
                lines.append(f"{acct_type}: {acct_num} - {balance}")
            account_info.update("\n".join(lines))
        else:
            account_info.update(f"Account: {atm_app.account_number}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu button presses."""
        button_id = event.button.id
        if button_id == "balance-btn":
            self._show_balance()
        elif button_id == "withdraw-btn":
            self.app.push_screen("withdrawal")
        elif button_id == "deposit-btn":
            self.app.push_screen("deposit")
        elif button_id == "transfer-btn":
            self.app.push_screen("transfer")
        elif button_id == "statement-btn":
            self.app.push_screen("statement")
        elif button_id == "change-pin-btn":
            self._show_pin_change()
        elif button_id == "logout-btn":
            self._logout()

    def _show_balance(self) -> None:
        """Fetch and display balance information."""
        self.run_worker(self._do_balance(), exclusive=True)

    async def _do_balance(self) -> None:
        """Call the balance inquiry API and display results."""
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        message = self.query_one("#menu-message", Static)
        message.update("Loading balance...")

        if not atm_app.accounts:
            message.update("[red]No accounts available.[/red]")
            return

        # Use the first account for balance inquiry
        first_account = atm_app.accounts[0]
        account_num = first_account.get("account_number", "")

        try:
            response = await atm_app.http_client.get(
                "/accounts/1/balance",
                headers=atm_app.session_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                account = data.get("account", {})
                transactions = data.get("recent_transactions", [])

                lines = [
                    f"Account: {account.get('account_number', account_num)}",
                    f"Type: {account.get('account_type', '')}",
                    f"Balance: {account.get('balance', '')}",
                    f"Available: {account.get('available_balance', '')}",
                    "",
                ]

                if transactions:
                    lines.append("--- Last 5 Transactions ---")
                    for txn in transactions:
                        txn_date = txn.get("date", "")[:10]
                        desc = txn.get("description", "")
                        amount = txn.get("amount", "")
                        lines.append(f"  {txn_date}  {desc:<25} {amount}")

                message.update("\n".join(lines))
            elif response.status_code == 401:
                message.update("[red]Session expired. Please log in again.[/red]")
            else:
                data = response.json()
                detail = data.get("detail", "Failed to retrieve balance.")
                message.update(f"[red]{detail}[/red]")

        except httpx.ConnectError:
            message.update("[red]Cannot connect to ATM server.[/red]")
        except httpx.HTTPError:
            message.update("[red]A network error occurred.[/red]")

    def _show_pin_change(self) -> None:
        """Show inline PIN change prompts."""
        message = self.query_one("#menu-message", Static)
        message.update(
            "PIN Change: This feature is available through the API.\n"
            "POST /api/v1/auth/pin/change with current_pin, new_pin, confirm_pin."
        )

    def _logout(self) -> None:
        """Log out and return to the welcome screen."""
        self.run_worker(self._do_logout(), exclusive=True)

    async def _do_logout(self) -> None:
        """Call the logout API endpoint."""
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        message = self.query_one("#menu-message", Static)

        with contextlib.suppress(httpx.HTTPError):
            await atm_app.http_client.post(
                "/auth/logout",
                headers=atm_app.session_headers(),
            )

        atm_app.clear_session()
        message.update("")
        self.app.switch_screen("welcome")
