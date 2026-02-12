"""Fund transfer screen.

Owner: UX Designer
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from textual.screen import Screen
from textual.widgets import Button, Input, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.atm.ui.app import ATMApp


class TransferScreen(Screen[None]):
    """Fund transfer screen with confirmation step."""

    def __init__(self) -> None:
        """Initialize the transfer screen."""
        super().__init__()
        self._pending_dest: str = ""
        self._pending_cents: int = 0
        self._confirmed: bool = False

    def compose(self) -> ComposeResult:
        """Compose the transfer screen layout."""
        with Static(classes="form-container"):
            yield Static("Transfer Funds", classes="title")
            yield Static("Destination Account Number:", classes="info-message")
            yield Input(
                placeholder="Enter destination account (e.g., 1000-0001-0002)",
                id="dest-account",
            )
            yield Static("Amount (in dollars):", classes="info-message")
            yield Input(
                placeholder="Enter transfer amount (e.g., 1000)",
                id="transfer-amount",
            )
            yield Button("Review Transfer", variant="primary", id="review-btn")
            yield Static("", id="transfer-result", classes="info-message")
            yield Button(
                "Confirm Transfer",
                variant="warning",
                id="confirm-btn",
                disabled=True,
            )
            yield Button("Back to Menu", variant="default", id="back-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "review-btn":
            self._review_transfer()
        elif event.button.id == "confirm-btn":
            self._confirm_transfer()
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle pressing Enter in input fields."""
        if event.input.id in ("dest-account", "transfer-amount"):
            self._review_transfer()

    def _review_transfer(self) -> None:
        """Validate inputs and show confirmation before executing."""
        dest_input = self.query_one("#dest-account", Input)
        amount_input = self.query_one("#transfer-amount", Input)
        result_label = self.query_one("#transfer-result", Static)
        confirm_btn = self.query_one("#confirm-btn", Button)

        dest = dest_input.value.strip()
        raw_amount = amount_input.value.strip().replace("$", "").replace(",", "")

        if not dest:
            result_label.update("[red]Please enter a destination account number.[/red]")
            confirm_btn.disabled = True
            return

        if not raw_amount:
            result_label.update("[red]Please enter a transfer amount.[/red]")
            confirm_btn.disabled = True
            return

        try:
            amount_cents = round(float(raw_amount) * 100)
        except ValueError:
            result_label.update("[red]Please enter a valid dollar amount.[/red]")
            confirm_btn.disabled = True
            return

        if amount_cents <= 0:
            result_label.update("[red]Amount must be greater than zero.[/red]")
            confirm_btn.disabled = True
            return

        self._pending_dest = dest
        self._pending_cents = amount_cents
        self._confirmed = False

        amount_display = f"${amount_cents / 100:,.2f}"
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        source = atm_app.account_number or "Your Account"

        result_label.update(
            f"Please confirm the following transfer:\n"
            f"  From: {source}\n"
            f"  To:   {dest}\n"
            f"  Amount: {amount_display}\n\n"
            f"Press 'Confirm Transfer' to proceed."
        )
        confirm_btn.disabled = False

    def _confirm_transfer(self) -> None:
        """Execute the confirmed transfer."""
        if not self._pending_dest or self._pending_cents <= 0:
            return
        self._confirmed = True
        self.run_worker(
            self._call_transfer(self._pending_dest, self._pending_cents),
            exclusive=True,
        )

    async def _call_transfer(self, dest_account: str, amount_cents: int) -> None:
        """Call the transfer API endpoint.

        Args:
            dest_account: Destination account number.
            amount_cents: Transfer amount in cents.
        """
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        result_label = self.query_one("#transfer-result", Static)
        confirm_btn = self.query_one("#confirm-btn", Button)
        confirm_btn.disabled = True
        result_label.update("Processing transfer...")

        try:
            response = await atm_app.http_client.post(
                "/transactions/transfer",
                json={
                    "destination_account_number": dest_account,
                    "amount_cents": amount_cents,
                },
                headers=atm_app.session_headers(),
            )

            if response.status_code in (200, 201):
                data = response.json()
                lines = [
                    "[green]Transfer Successful[/green]",
                    f"Amount: {data.get('amount', '')}",
                    f"From: {data.get('source_account', '')}",
                    f"To: {data.get('destination_account', '')}",
                    f"Balance After: {data.get('balance_after', '')}",
                    f"Reference: {data.get('reference_number', '')}",
                ]
                result_label.update("\n".join(lines))
            elif response.status_code == 401:
                result_label.update("[red]Session expired. Please log in again.[/red]")
            else:
                data = response.json()
                detail = data.get("detail", "Transfer failed.")
                result_label.update(f"[red]{detail}[/red]")

        except httpx.ConnectError:
            result_label.update("[red]Cannot connect to ATM server.[/red]")
        except httpx.HTTPError:
            result_label.update("[red]A network error occurred.[/red]")
