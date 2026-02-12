"""Unit tests for the Withdrawal screen."""

from textual.widgets import Button, Input, Static

from src.atm.ui.app import ATMApp
from src.atm.ui.screens.withdrawal import QUICK_AMOUNTS


def _setup_and_push(app):
    """Set up session state and push withdrawal screen."""
    app.session_id = "test-session-123"
    app.customer_name = "Alice"
    app.account_number = "1000-0001-0001"
    app.accounts = [{"account_number": "1000-0001-0001"}]


class TestWithdrawalScreen:
    async def test_title_displayed(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            title = pilot.app.screen.query_one(".title", Static)
            assert "Withdrawal" in str(title.render())

    async def test_quick_amount_buttons_rendered(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            for amount in QUICK_AMOUNTS:
                btn = pilot.app.screen.query_one(f"#quick-{amount}", Button)
                assert f"${amount}" in str(btn.label)

    async def test_custom_amount_input_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#custom-amount", Input)
            assert inp is not None

    async def test_empty_custom_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            pilot.app.screen.query_one("#custom-withdraw-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#withdraw-result", Static)
            assert "enter an amount" in str(result.render()).lower()

    async def test_non_numeric_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#custom-amount", Input)
            inp.value = "abc"
            pilot.app.screen.query_one("#custom-withdraw-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#withdraw-result", Static)
            assert "valid" in str(result.render()).lower()

    async def test_zero_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#custom-amount", Input)
            inp.value = "0"
            pilot.app.screen.query_one("#custom-withdraw-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#withdraw-result", Static)
            assert "greater than zero" in str(result.render()).lower()

    async def test_non_multiple_of_20_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#custom-amount", Input)
            inp.value = "55"
            pilot.app.screen.query_one("#custom-withdraw-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#withdraw-result", Static)
            assert "multiple of $20" in str(result.render()).lower()

    async def test_back_button_pops_screen(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("withdrawal")
            await pilot.pause()
            pilot.app.screen.query_one("#back-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.main_menu import MainMenuScreen

            assert isinstance(pilot.app.screen, MainMenuScreen)
