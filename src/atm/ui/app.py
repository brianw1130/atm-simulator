"""Main Textual application entry point.

Owner: UX Designer

Launches the ATM terminal UI with screen navigation and session management.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, ClassVar

import httpx
from textual.app import App
from textual.binding import Binding
from textual.widgets import Footer, Header

from src.atm.ui.screens.deposit import DepositScreen
from src.atm.ui.screens.main_menu import MainMenuScreen
from src.atm.ui.screens.pin_entry import PinEntryScreen
from src.atm.ui.screens.statement import StatementScreen
from src.atm.ui.screens.transfer import TransferScreen
from src.atm.ui.screens.welcome import WelcomeScreen
from src.atm.ui.screens.withdrawal import WithdrawalScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.screen import Screen

API_BASE_URL = "http://localhost:8000/api/v1"
SESSION_TIMEOUT_SECONDS = 120


class ATMApp(App[None]):
    """ATM Simulator terminal application.

    Manages screen navigation, session state, and API communication.
    """

    TITLE = "ATM Simulator"
    CSS = """
    Screen {
        align: center middle;
    }

    #banner {
        text-align: center;
        color: $accent;
        margin-bottom: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .error-message {
        color: red;
        text-align: center;
        margin: 1 0;
    }

    .success-message {
        color: green;
        text-align: center;
        margin: 1 0;
    }

    .info-message {
        color: $text;
        text-align: center;
        margin: 1 0;
    }

    .form-container {
        width: 60;
        height: auto;
        padding: 1 2;
        border: solid $accent;
        background: $surface;
    }

    .form-container Input {
        margin-bottom: 1;
    }

    .form-container Button {
        width: 100%;
        margin-top: 1;
    }

    .menu-container {
        width: 60;
        height: auto;
        padding: 1 2;
        border: solid $accent;
        background: $surface;
    }

    .menu-container Button {
        width: 100%;
        margin-bottom: 1;
    }

    .result-container {
        width: 70;
        height: auto;
        padding: 1 2;
        border: solid $accent;
        background: $surface;
    }

    .quick-buttons {
        layout: grid;
        grid-size: 3 2;
        grid-gutter: 1;
        margin-bottom: 1;
    }

    .quick-buttons Button {
        width: 100%;
    }

    DataTable {
        height: auto;
        max-height: 12;
        margin: 1 0;
    }

    .loading {
        text-align: center;
        color: $text-muted;
        margin: 1 0;
    }

    #account-selector {
        margin-bottom: 1;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit", show=True),
    ]

    SCREENS: ClassVar[dict[str, type[Screen[object]]]] = {
        "welcome": WelcomeScreen,
        "pin_entry": PinEntryScreen,
        "main_menu": MainMenuScreen,
        "withdrawal": WithdrawalScreen,
        "deposit": DepositScreen,
        "transfer": TransferScreen,
        "statement": StatementScreen,
    }

    def __init__(self) -> None:
        """Initialize the ATM application."""
        super().__init__()
        self.session_id: str | None = None
        self.customer_name: str = ""
        self.account_number: str = ""
        self.card_number: str = ""
        self.accounts: list[dict[str, Any]] = []
        self._http_client: httpx.AsyncClient | None = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for API calls.

        Returns:
            An httpx.AsyncClient instance.
        """
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=API_BASE_URL,
                timeout=30.0,
            )
        return self._http_client

    def session_headers(self) -> dict[str, str]:
        """Build headers with the session token.

        Returns:
            Dictionary with X-Session-ID header if session exists.
        """
        if self.session_id:
            return {"X-Session-ID": self.session_id}
        return {}

    def clear_session(self) -> None:
        """Clear all session state."""
        self.session_id = None
        self.customer_name = ""
        self.account_number = ""
        self.card_number = ""
        self.accounts = []

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header(show_clock=True)
        yield Footer()

    def on_mount(self) -> None:
        """Navigate to the welcome screen on startup."""
        self.push_screen("welcome")

    async def action_quit(self) -> None:
        """Quit the application, logging out if needed."""
        if self.session_id:
            with contextlib.suppress(httpx.HTTPError):
                await self.http_client.post(
                    "/auth/logout",
                    headers=self.session_headers(),
                )
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        self.exit()


def run_atm() -> None:
    """Launch the ATM terminal UI application."""
    app = ATMApp()
    app.run()


if __name__ == "__main__":
    run_atm()
