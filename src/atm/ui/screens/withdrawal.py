"""Cash withdrawal screen with quick-select and custom amounts.

Owner: UX Designer
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.atm.ui.app import ATMApp

QUICK_AMOUNTS = [20, 40, 60, 100, 200]


class WithdrawalScreen(Screen[None]):
    """Cash withdrawal screen with quick-select and custom amount entry."""

    def compose(self) -> ComposeResult:
        """Compose the withdrawal screen layout."""
        with Static(classes="form-container"):
            yield Static("Cash Withdrawal", classes="title")
            yield Static("Quick Withdraw:", classes="info-message")
            with Horizontal(classes="quick-buttons"):
                for amount in QUICK_AMOUNTS:
                    yield Button(
                        f"${amount}",
                        variant="primary",
                        id=f"quick-{amount}",
                    )
            yield Static("Or enter a custom amount (multiple of $20):", classes="info-message")
            yield Input(
                placeholder="Enter amount in dollars (e.g., 260)",
                id="custom-amount",
            )
            yield Button("Withdraw Custom Amount", variant="primary", id="custom-withdraw-btn")
            yield Static("", id="withdraw-result", classes="info-message")
            yield Button("Back to Menu", variant="default", id="back-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id and button_id.startswith("quick-"):
            amount_str = button_id.replace("quick-", "")
            amount_dollars = int(amount_str)
            self._do_withdraw(amount_dollars)
        elif button_id == "custom-withdraw-btn":
            self._submit_custom()
        elif button_id == "back-btn":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle pressing Enter in the custom amount input."""
        if event.input.id == "custom-amount":
            self._submit_custom()

    def _submit_custom(self) -> None:
        """Validate and submit a custom withdrawal amount."""
        amount_input = self.query_one("#custom-amount", Input)
        result_label = self.query_one("#withdraw-result", Static)
        raw = amount_input.value.strip().replace("$", "").replace(",", "")

        if not raw:
            result_label.update("[red]Please enter an amount.[/red]")
            return

        try:
            amount_dollars = int(raw)
        except ValueError:
            result_label.update("[red]Please enter a valid whole dollar amount.[/red]")
            return

        if amount_dollars <= 0:
            result_label.update("[red]Amount must be greater than zero.[/red]")
            return

        if amount_dollars % 20 != 0:
            result_label.update("[red]Amount must be a multiple of $20.[/red]")
            return

        self._do_withdraw(amount_dollars)

    def _do_withdraw(self, amount_dollars: int) -> None:
        """Start the withdrawal API call.

        Args:
            amount_dollars: The withdrawal amount in whole dollars.
        """
        self.run_worker(self._call_withdraw(amount_dollars), exclusive=True)

    async def _call_withdraw(self, amount_dollars: int) -> None:
        """Call the withdrawal API endpoint.

        Args:
            amount_dollars: The withdrawal amount in whole dollars.
        """
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        result_label = self.query_one("#withdraw-result", Static)
        result_label.update("Processing withdrawal...")

        amount_cents = amount_dollars * 100

        try:
            response = await atm_app.http_client.post(
                "/transactions/withdraw",
                json={"amount_cents": amount_cents},
                headers=atm_app.session_headers(),
            )

            if response.status_code in (200, 201):
                data = response.json()
                denominations = data.get("denominations", {})
                lines = [
                    "[green]Withdrawal Successful[/green]",
                    f"Amount: {data.get('amount', '')}",
                    f"Balance After: {data.get('balance_after', '')}",
                    f"Reference: {data.get('reference_number', '')}",
                    "",
                    "Denomination Breakdown:",
                    f"  $20 bills: {denominations.get('twenties', 0)}",
                    f"  Total bills: {denominations.get('total_bills', 0)}",
                ]
                result_label.update("\n".join(lines))
            elif response.status_code == 401:
                result_label.update("[red]Session expired. Please log in again.[/red]")
            else:
                data = response.json()
                detail = data.get("detail", "Withdrawal failed.")
                result_label.update(f"[red]{detail}[/red]")

        except httpx.ConnectError:
            result_label.update("[red]Cannot connect to ATM server.[/red]")
        except httpx.HTTPError:
            result_label.update("[red]A network error occurred.[/red]")
