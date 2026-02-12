"""Unit tests for the Transfer screen."""

from textual.widgets import Button, Input, Static

from src.atm.ui.app import ATMApp


def _setup_and_push(app):
    """Set up session state."""
    app.session_id = "test-session-123"
    app.customer_name = "Alice"
    app.account_number = "1000-0001-0001"
    app.accounts = [{"account_number": "1000-0001-0001"}]


class TestTransferScreen:
    async def test_title_displayed(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            title = pilot.app.screen.query_one(".title", Static)
            assert "Transfer" in str(title.render())

    async def test_destination_input_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#dest-account", Input)
            assert inp is not None

    async def test_amount_input_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            inp = pilot.app.screen.query_one("#transfer-amount", Input)
            assert inp is not None

    async def test_confirm_button_initially_disabled(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            btn = pilot.app.screen.query_one("#confirm-btn", Button)
            assert btn.disabled is True

    async def test_empty_destination_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            amount_inp = pilot.app.screen.query_one("#transfer-amount", Input)
            amount_inp.value = "100"
            pilot.app.screen.query_one("#review-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#transfer-result", Static)
            assert "destination" in str(result.render()).lower()

    async def test_empty_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            dest_inp = pilot.app.screen.query_one("#dest-account", Input)
            dest_inp.value = "1000-0001-0002"
            pilot.app.screen.query_one("#review-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#transfer-result", Static)
            assert "enter a transfer amount" in str(result.render()).lower()

    async def test_zero_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            dest_inp = pilot.app.screen.query_one("#dest-account", Input)
            dest_inp.value = "1000-0001-0002"
            amount_inp = pilot.app.screen.query_one("#transfer-amount", Input)
            amount_inp.value = "0"
            pilot.app.screen.query_one("#review-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#transfer-result", Static)
            assert "greater than zero" in str(result.render()).lower()

    async def test_review_shows_confirmation(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            dest_inp = pilot.app.screen.query_one("#dest-account", Input)
            dest_inp.value = "1000-0001-0002"
            amount_inp = pilot.app.screen.query_one("#transfer-amount", Input)
            amount_inp.value = "500"
            pilot.app.screen.query_one("#review-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#transfer-result", Static)
            text = str(result.render())
            assert "1000-0001-0002" in text
            assert "$500.00" in text
            confirm_btn = pilot.app.screen.query_one("#confirm-btn", Button)
            assert confirm_btn.disabled is False

    async def test_non_numeric_amount_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            dest_inp = pilot.app.screen.query_one("#dest-account", Input)
            dest_inp.value = "1000-0001-0002"
            amount_inp = pilot.app.screen.query_one("#transfer-amount", Input)
            amount_inp.value = "abc"
            pilot.app.screen.query_one("#review-btn", Button).press()
            await pilot.pause()
            result = pilot.app.screen.query_one("#transfer-result", Static)
            assert "valid" in str(result.render()).lower()

    async def test_back_button_pops_screen(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_and_push(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.push_screen("transfer")
            await pilot.pause()
            pilot.app.screen.query_one("#back-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.main_menu import MainMenuScreen

            assert isinstance(pilot.app.screen, MainMenuScreen)
