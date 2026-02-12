"""PIN entry screen with masked input.

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


class PinEntryScreen(Screen[None]):
    """PIN entry screen for authentication."""

    def compose(self) -> ComposeResult:
        """Compose the PIN entry layout."""
        with Static(classes="form-container"):
            yield Static("Enter Your PIN", classes="title")
            yield Static("", id="card-display", classes="info-message")
            yield Input(
                placeholder="Enter PIN",
                password=True,
                max_length=6,
                id="pin-input",
            )
            yield Static("", id="pin-error", classes="error-message")
            yield Button("Enter", variant="primary", id="enter-btn")
            yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        """Display the card number when the screen mounts."""
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        card_display = self.query_one("#card-display", Static)
        card = atm_app.card_number
        masked = "X" * (len(card) - 4) + card[-4:] if len(card) > 4 else card
        card_display.update(f"Card: {masked}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "enter-btn":
            self._submit_pin()
        elif event.button.id == "cancel-btn":
            self.app.switch_screen("welcome")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle pressing Enter in the PIN input."""
        if event.input.id == "pin-input":
            self._submit_pin()

    def _submit_pin(self) -> None:
        """Validate PIN and call login API."""
        pin_input = self.query_one("#pin-input", Input)
        pin = pin_input.value.strip()
        error_label = self.query_one("#pin-error", Static)

        if not pin or not pin.isdigit() or len(pin) < 4:
            error_label.update("Please enter a valid 4-6 digit PIN.")
            return

        error_label.update("")
        self.run_worker(self._do_login(pin), exclusive=True)

    async def _do_login(self, pin: str) -> None:
        """Call the login API endpoint.

        Args:
            pin: The PIN entered by the user.
        """
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        error_label = self.query_one("#pin-error", Static)
        enter_btn = self.query_one("#enter-btn", Button)
        enter_btn.disabled = True

        try:
            response = await atm_app.http_client.post(
                "/auth/login",
                json={
                    "card_number": atm_app.card_number,
                    "pin": pin,
                },
            )

            if response.status_code == 200:
                data = response.json()
                atm_app.session_id = data["session_id"]
                atm_app.customer_name = data["customer_name"]
                atm_app.account_number = data["account_number"]

                # Fetch the customer's accounts
                try:
                    accounts_resp = await atm_app.http_client.get(
                        "/accounts",
                        headers=atm_app.session_headers(),
                    )
                    if accounts_resp.status_code == 200:
                        atm_app.accounts = accounts_resp.json().get("accounts", [])
                except httpx.HTTPError:
                    atm_app.accounts = []

                self.app.switch_screen("main_menu")
            else:
                data = response.json()
                detail = data.get("detail", "Authentication failed.")
                error_label.update(detail)

        except httpx.ConnectError:
            error_label.update("Cannot connect to ATM server. Please try again later.")
        except httpx.HTTPError:
            error_label.update("A network error occurred. Please try again.")
        finally:
            enter_btn.disabled = False
