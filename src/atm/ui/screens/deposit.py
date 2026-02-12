"""Deposit screen for cash and check deposits.

Owner: UX Designer
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from textual.screen import Screen
from textual.widgets import Button, Input, RadioButton, RadioSet, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.atm.ui.app import ATMApp


class DepositScreen(Screen[None]):
    """Deposit screen supporting cash and check deposits."""

    def compose(self) -> ComposeResult:
        """Compose the deposit screen layout."""
        with Static(classes="form-container"):
            yield Static("Make a Deposit", classes="title")
            yield Static("Deposit Type:", classes="info-message")
            with RadioSet(id="deposit-type"):
                yield RadioButton("Cash Deposit", value=True, id="radio-cash")
                yield RadioButton("Check Deposit", id="radio-check")
            yield Static("Amount (in dollars):", classes="info-message")
            yield Input(
                placeholder="Enter deposit amount (e.g., 500)",
                id="deposit-amount",
            )
            yield Static("Check Number:", id="check-label", classes="info-message")
            yield Input(
                placeholder="Enter check number",
                id="check-number",
                disabled=True,
            )
            yield Button("Submit Deposit", variant="primary", id="deposit-btn")
            yield Static("", id="deposit-result", classes="info-message")
            yield Button("Back to Menu", variant="default", id="back-btn")

    def on_mount(self) -> None:
        """Initialize the screen state."""
        self._update_check_field_visibility()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle deposit type toggle."""
        self._update_check_field_visibility()

    def _update_check_field_visibility(self) -> None:
        """Show or hide the check number field based on deposit type."""
        radio_set = self.query_one("#deposit-type", RadioSet)
        check_input = self.query_one("#check-number", Input)
        check_label = self.query_one("#check-label", Static)

        # The pressed index indicates which radio is selected
        is_check = radio_set.pressed_index == 1
        check_input.disabled = not is_check
        if not is_check:
            check_input.value = ""
            check_label.update("")
        else:
            check_label.update("Check Number:")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "deposit-btn":
            self._submit_deposit()
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle pressing Enter in an input field."""
        if event.input.id in ("deposit-amount", "check-number"):
            self._submit_deposit()

    def _submit_deposit(self) -> None:
        """Validate inputs and submit the deposit."""
        amount_input = self.query_one("#deposit-amount", Input)
        check_input = self.query_one("#check-number", Input)
        result_label = self.query_one("#deposit-result", Static)
        radio_set = self.query_one("#deposit-type", RadioSet)

        raw_amount = amount_input.value.strip().replace("$", "").replace(",", "")

        if not raw_amount:
            result_label.update("[red]Please enter a deposit amount.[/red]")
            return

        try:
            amount_cents = round(float(raw_amount) * 100)
        except ValueError:
            result_label.update("[red]Please enter a valid dollar amount.[/red]")
            return

        if amount_cents <= 0:
            result_label.update("[red]Amount must be greater than zero.[/red]")
            return

        is_check = radio_set.pressed_index == 1
        deposit_type = "check" if is_check else "cash"

        check_number: str | None = None
        if is_check:
            check_number = check_input.value.strip()
            if not check_number:
                result_label.update("[red]Check number is required for check deposits.[/red]")
                return

        self.run_worker(
            self._call_deposit(amount_cents, deposit_type, check_number),
            exclusive=True,
        )

    async def _call_deposit(
        self,
        amount_cents: int,
        deposit_type: str,
        check_number: str | None,
    ) -> None:
        """Call the deposit API endpoint.

        Args:
            amount_cents: Deposit amount in cents.
            deposit_type: 'cash' or 'check'.
            check_number: Check number (for check deposits).
        """
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        result_label = self.query_one("#deposit-result", Static)
        result_label.update("Processing deposit...")

        payload: dict[str, object] = {
            "amount_cents": amount_cents,
            "deposit_type": deposit_type,
        }
        if check_number:
            payload["check_number"] = check_number

        try:
            response = await atm_app.http_client.post(
                "/transactions/deposit",
                json=payload,
                headers=atm_app.session_headers(),
            )

            if response.status_code in (200, 201):
                data = response.json()
                lines = [
                    "[green]Deposit Accepted[/green]",
                    f"Type: {data.get('transaction_type', '')}",
                    f"Amount: {data.get('amount', '')}",
                    f"Balance After: {data.get('balance_after', '')}",
                    f"Reference: {data.get('reference_number', '')}",
                    "",
                    "Hold Information:",
                    f"  Available Immediately: {data.get('available_immediately', '')}",
                    f"  Amount on Hold: {data.get('held_amount', '')}",
                ]
                hold_until = data.get("hold_until")
                if hold_until:
                    lines.append(f"  Hold Expires: {hold_until[:10]}")
                result_label.update("\n".join(lines))
            elif response.status_code == 401:
                result_label.update("[red]Session expired. Please log in again.[/red]")
            else:
                data = response.json()
                detail = data.get("detail", "Deposit failed.")
                result_label.update(f"[red]{detail}[/red]")

        except httpx.ConnectError:
            result_label.update("[red]Cannot connect to ATM server.[/red]")
        except httpx.HTTPError:
            result_label.update("[red]A network error occurred.[/red]")
