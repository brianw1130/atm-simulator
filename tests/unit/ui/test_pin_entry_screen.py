"""Unit tests for the PIN entry screen."""

from textual.widgets import Button, Input, Static

from src.atm.ui.app import ATMApp


async def _navigate_to_pin_entry(pilot):
    """Navigate past the welcome screen to the PIN entry screen."""
    await pilot.pause()
    card_input = pilot.app.screen.query_one("#card-number-input", Input)
    card_input.value = "1000-0001-0001"
    pilot.app.screen.query_one("#insert-card-btn", Button).press()
    await pilot.pause()


class TestPinEntryScreen:
    async def test_pin_input_is_masked(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            pin_input = pilot.app.screen.query_one("#pin-input", Input)
            assert pin_input.password is True

    async def test_pin_input_max_length_is_6(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            pin_input = pilot.app.screen.query_one("#pin-input", Input)
            assert pin_input.max_length == 6

    async def test_card_number_displayed_masked(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            card_display = pilot.app.screen.query_one("#card-display", Static)
            display_text = str(card_display.render())
            assert "0001" in display_text
            assert "X" in display_text

    async def test_empty_pin_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            pilot.app.screen.query_one("#enter-btn", Button).press()
            await pilot.pause()
            error_label = pilot.app.screen.query_one("#pin-error", Static)
            assert "valid" in str(error_label.render()).lower()

    async def test_short_pin_shows_error(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            pin_input = pilot.app.screen.query_one("#pin-input", Input)
            pin_input.value = "12"
            pilot.app.screen.query_one("#enter-btn", Button).press()
            await pilot.pause()
            error_label = pilot.app.screen.query_one("#pin-error", Static)
            assert "valid" in str(error_label.render()).lower()

    async def test_cancel_returns_to_welcome(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            pilot.app.screen.query_one("#cancel-btn", Button).press()
            await pilot.pause()
            from src.atm.ui.screens.welcome import WelcomeScreen

            assert isinstance(pilot.app.screen, WelcomeScreen)

    async def test_enter_button_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            btn = pilot.app.screen.query_one("#enter-btn", Button)
            assert "Enter" in str(btn.label)

    async def test_cancel_button_exists(self):
        async with ATMApp().run_test(size=(120, 50)) as pilot:
            await _navigate_to_pin_entry(pilot)
            btn = pilot.app.screen.query_one("#cancel-btn", Button)
            assert "Cancel" in str(btn.label)
