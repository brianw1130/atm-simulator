"""Welcome / card insertion screen.

Owner: UX Designer
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Button, Input, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.atm.ui.app import ATMApp

WELCOME_BANNER = """\
 ╔══════════════════════════════════════╗
 ║        WELCOME TO ATM SIMULATOR     ║
 ║                                     ║
 ║     Please insert your card below   ║
 ╚══════════════════════════════════════╝
"""


class WelcomeScreen(Screen[None]):
    """Welcome screen where the user enters their card number."""

    def compose(self) -> ComposeResult:
        """Compose the welcome screen layout."""
        with Static(classes="form-container"):
            yield Static(WELCOME_BANNER, id="banner")
            yield Static("Card Number:", classes="info-message")
            yield Input(
                placeholder="Enter your card number (e.g., 1000-0001-0001)",
                id="card-number-input",
            )
            yield Static("", id="error-label", classes="error-message")
            yield Button("Insert Card", variant="primary", id="insert-card-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the Insert Card button press."""
        if event.button.id == "insert-card-btn":
            self._submit_card()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle pressing Enter in the card number input."""
        if event.input.id == "card-number-input":
            self._submit_card()

    def _submit_card(self) -> None:
        """Validate and store the card number, then navigate to PIN entry."""
        card_input = self.query_one("#card-number-input", Input)
        error_label = self.query_one("#error-label", Static)
        card_number = card_input.value.strip()

        if not card_number:
            error_label.update("Please enter a card number.")
            return

        atm_app: ATMApp = self.app  # type: ignore[assignment]
        atm_app.card_number = card_number
        error_label.update("")
        self.app.switch_screen("pin_entry")
