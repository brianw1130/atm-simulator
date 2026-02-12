"""Unit tests for the Welcome screen."""

from textual.widgets import Button, Input, Static

from src.atm.ui.app import ATMApp


class TestWelcomeScreen:
    async def test_banner_is_rendered(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            banner = pilot.app.screen.query_one("#banner", Static)
            assert "WELCOME" in str(banner.render())

    async def test_card_number_input_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card_input = pilot.app.screen.query_one("#card-number-input", Input)
            assert card_input is not None

    async def test_insert_card_button_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            btn = pilot.app.screen.query_one("#insert-card-btn", Button)
            assert "Insert Card" in str(btn.label)

    async def test_empty_card_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            pilot.app.screen.query_one("#insert-card-btn", Button).press()
            await pilot.pause()
            error_label = pilot.app.screen.query_one("#error-label", Static)
            assert "enter a card number" in str(error_label.render()).lower()

    async def test_valid_card_navigates_to_pin_entry(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card_input = pilot.app.screen.query_one("#card-number-input", Input)
            card_input.value = "1000-0001-0001"
            pilot.app.screen.query_one("#insert-card-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.pin_entry import PinEntryScreen

            assert isinstance(pilot.app.screen, PinEntryScreen)

    async def test_card_number_stored_in_app(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card_input = pilot.app.screen.query_one("#card-number-input", Input)
            card_input.value = "4000-0001-0001"
            pilot.app.screen.query_one("#insert-card-btn", Button).press()
            await pilot.pause()
            assert pilot.app.card_number == "4000-0001-0001"
