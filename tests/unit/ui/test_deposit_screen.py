"""Unit tests for the Deposit screen."""

from textual.widgets import Button, Input, RadioSet, Static

from src.atm.ui.app import ATMApp


def _setup_and_push(app):
    """Set up session state."""
    app.session_id = "test-session-123"
    app.customer_name = "Alice"
    app.account_number = "1000-0001-0001"
    app.accounts = [{"account_number": "1000-0001-0001"}]


class TestDepositScreen:
    async def test_title_displayed(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            title = pilot.app.screen.query_one(".title", Static)
            assert "Deposit" in str(title.render())

    async def test_deposit_type_radio_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            radio = pilot.app.screen.query_one("#deposit-type", RadioSet)
            assert radio is not None

    async def test_amount_input_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#deposit-amount", Input)
            assert inp is not None

    async def test_check_number_input_disabled_for_cash(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            check_inp = pilot.app.screen.query_one("#check-number", Input)
            assert check_inp.disabled is True

    async def test_empty_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            pilot.app.screen.query_one("#deposit-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#deposit-result", Static)
            assert "enter a deposit amount" in str(result.render()).lower()

    async def test_non_numeric_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#deposit-amount", Input)
            inp.value = "xyz"
            pilot.app.screen.query_one("#deposit-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#deposit-result", Static)
            assert "valid" in str(result.render()).lower()

    async def test_zero_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#deposit-amount", Input)
            inp.value = "0"
            pilot.app.screen.query_one("#deposit-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#deposit-result", Static)
            assert "greater than zero" in str(result.render()).lower()

    async def test_back_button_pops_screen(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("deposit")
            await pilot.pause()
            pilot.app.screen.query_one("#back-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.main_menu import MainMenuScreen

            assert isinstance(pilot.app.screen, MainMenuScreen)
