"""Account statement request screen.

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


class StatementScreen(Screen[None]):
    """Statement generation screen with period selection."""

    def compose(self) -> ComposeResult:
        """Compose the statement screen layout."""
        with Static(classes="form-container"):
            yield Static("Account Statement", classes="title")
            yield Static("Select a period or enter custom dates:", classes="info-message")
            yield Button("Last 7 Days", variant="primary", id="period-7")
            yield Button("Last 30 Days", variant="primary", id="period-30")
            yield Button("Last 90 Days", variant="primary", id="period-90")
            yield Static("Custom Date Range:", classes="info-message")
            yield Static("Start Date (YYYY-MM-DD):", classes="info-message")
            yield Input(
                placeholder="e.g., 2026-01-01",
                id="start-date",
            )
            yield Static("End Date (YYYY-MM-DD):", classes="info-message")
            yield Input(
                placeholder="e.g., 2026-01-31",
                id="end-date",
            )
            yield Button("Generate Custom Statement", variant="primary", id="custom-stmt-btn")
            yield Static("", id="statement-result", classes="info-message")
            yield Button("Back to Menu", variant="default", id="back-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id == "period-7":
            self._generate_by_days(7)
        elif button_id == "period-30":
            self._generate_by_days(30)
        elif button_id == "period-90":
            self._generate_by_days(90)
        elif button_id == "custom-stmt-btn":
            self._generate_custom()
        elif button_id == "back-btn":
            self.app.pop_screen()

    def _generate_by_days(self, days: int) -> None:
        """Generate a statement for a relative period.

        Args:
            days: Number of days to include.
        """
        self.run_worker(self._call_statement(days=days), exclusive=True)

    def _generate_custom(self) -> None:
        """Validate custom date inputs and generate statement."""
        start_input = self.query_one("#start-date", Input)
        end_input = self.query_one("#end-date", Input)
        result_label = self.query_one("#statement-result", Static)

        start = start_input.value.strip()
        end = end_input.value.strip()

        if not start or not end:
            result_label.update("[red]Both start and end dates are required.[/red]")
            return

        # Basic date format validation
        for label, val in [("Start date", start), ("End date", end)]:
            parts = val.split("-")
            if len(parts) != 3 or not all(p.isdigit() for p in parts):
                result_label.update(f"[red]{label} must be in YYYY-MM-DD format.[/red]")
                return

        self.run_worker(
            self._call_statement(start_date=start, end_date=end),
            exclusive=True,
        )

    async def _call_statement(
        self,
        days: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> None:
        """Call the statement generation API endpoint.

        Args:
            days: Relative period in days (used if start_date/end_date not set).
            start_date: Custom range start date (YYYY-MM-DD).
            end_date: Custom range end date (YYYY-MM-DD).
        """
        atm_app: ATMApp = self.app  # type: ignore[assignment]
        result_label = self.query_one("#statement-result", Static)
        result_label.update("Generating statement...")

        payload: dict[str, object] = {}
        if start_date and end_date:
            payload["start_date"] = start_date
            payload["end_date"] = end_date
        elif days:
            payload["days"] = days

        try:
            response = await atm_app.http_client.post(
                "/statements/generate",
                json=payload,
                headers=atm_app.session_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                lines = [
                    "[green]Statement Generated Successfully[/green]",
                    f"Period: {data.get('period', '')}",
                    f"Transactions: {data.get('transaction_count', 0)}",
                    f"Opening Balance: {data.get('opening_balance', '')}",
                    f"Closing Balance: {data.get('closing_balance', '')}",
                    f"File: {data.get('file_path', '')}",
                ]
                result_label.update("\n".join(lines))
            elif response.status_code == 401:
                result_label.update("[red]Session expired. Please log in again.[/red]")
            else:
                data = response.json()
                detail = data.get("detail", "Statement generation failed.")
                result_label.update(f"[red]{detail}[/red]")

        except httpx.ConnectError:
            result_label.update("[red]Cannot connect to ATM server.[/red]")
        except httpx.HTTPError:
            result_label.update("[red]A network error occurred.[/red]")
