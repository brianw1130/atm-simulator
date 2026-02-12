"""Unit tests for the Statement screen."""

from textual.widgets import Button, Input, Static

from src.atm.ui.app import ATMApp


def _setup_and_push(app):
    """Set up session state."""
    app.session_id = "test-session-123"
    app.customer_name = "Alice"
    app.account_number = "1000-0001-0001"
    app.accounts = [{"account_number": "1000-0001-0001"}]


class TestStatementScreen:
    async def test_title_displayed(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("statement")
            await pilot.pause()
            title = pilot.app.screen.query_one(".title", Static)
            assert "Statement" in str(title.render())

    async def test_period_buttons_exist(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("statement")
            await pilot.pause()
            for period_id in ("period-7", "period-30", "period-90"):
                btn = pilot.app.screen.query_one(f"#{period_id}", Button)
                assert btn is not None

    async def test_date_inputs_exist(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("statement")
            await pilot.pause()
            start_inp = pilot.app.screen.query_one("#start-date", Input)
            end_inp = pilot.app.screen.query_one("#end-date", Input)
            assert start_inp is not None
            assert end_inp is not None

    async def test_custom_with_empty_dates_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("statement")
            await pilot.pause()
            pilot.app.screen.query_one("#custom-stmt-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#statement-result", Static)
            assert "required" in str(result.render()).lower()

    async def test_custom_with_invalid_date_format_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("statement")
            await pilot.pause()
            start_inp = pilot.app.screen.query_one("#start-date", Input)
            end_inp = pilot.app.screen.query_one("#end-date", Input)
            start_inp.value = "2026/01/01"
            end_inp.value = "2026-01-31"
            pilot.app.screen.query_one("#custom-stmt-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#statement-result", Static)
            assert "YYYY-MM-DD" in str(result.render())

    async def test_back_button_pops_screen(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("statement")
            await pilot.pause()
            pilot.app.screen.query_one("#back-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.main_menu import MainMenuScreen

            assert isinstance(pilot.app.screen, MainMenuScreen)
