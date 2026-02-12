"""Unit tests for the Main Menu screen."""

from textual.widgets import Button, Static

from src.atm.ui.app import ATMApp


def _setup_session(app):
    """Set up a mock authenticated session on the app."""
    app.session_id = "test-session-123"
    app.customer_name = "Alice Johnson"
    app.account_number = "1000-0001-0001"
    app.accounts = [
        {
            "account_number": "1000-0001-0001",
            "account_type": "CHECKING",
            "balance": "$5,250.00",
            "available_balance": "$5,250.00",
        }
    ]


class TestMainMenuScreen:
    async def test_greeting_shows_customer_name(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            greeting = pilot.app.screen.query_one("#greeting", Static)
            assert "Alice Johnson" in str(greeting.render())

    async def test_account_info_displayed(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            info = pilot.app.screen.query_one("#account-info", Static)
            assert "CHECKING" in str(info.render())

    async def test_all_menu_buttons_exist(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()

            expected_ids = [
                "balance-btn",
                "withdraw-btn",
                "deposit-btn",
                "transfer-btn",
                "statement-btn",
                "change-pin-btn",
                "logout-btn",
            ]
            for btn_id in expected_ids:
                btn = pilot.app.screen.query_one(f"#{btn_id}", Button)
                assert btn is not None

    async def test_withdraw_button_navigates(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.screen.query_one("#withdraw-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.withdrawal import WithdrawalScreen

            assert isinstance(pilot.app.screen, WithdrawalScreen)

    async def test_deposit_button_navigates(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.screen.query_one("#deposit-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.deposit import DepositScreen

            assert isinstance(pilot.app.screen, DepositScreen)

    async def test_transfer_button_navigates(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.screen.query_one("#transfer-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.transfer import TransferScreen

            assert isinstance(pilot.app.screen, TransferScreen)

    async def test_statement_button_navigates(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.screen.query_one("#statement-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.statement import StatementScreen

            assert isinstance(pilot.app.screen, StatementScreen)

    async def test_change_pin_shows_info(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            _setup_session(pilot.app)
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            pilot.app.screen.query_one("#change-pin-btn", Button).press()
            await pilot.pause()
            message = pilot.app.screen.query_one("#menu-message", Static)
            assert "PIN" in str(message.render())

    async def test_account_info_fallback_when_no_accounts(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            pilot.app.session_id = "test-session-123"
            pilot.app.customer_name = "Bob Williams"
            pilot.app.account_number = "1000-0002-0001"
            pilot.app.accounts = []
            pilot.app.switch_screen("main_menu")
            await pilot.pause()
            info = pilot.app.screen.query_one("#account-info", Static)
            assert "1000-0002-0001" in str(info.render())
