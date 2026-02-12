"""Textual UI screens for ATM operations."""

from src.atm.ui.screens.deposit import DepositScreen
from src.atm.ui.screens.main_menu import MainMenuScreen
from src.atm.ui.screens.pin_entry import PinEntryScreen
from src.atm.ui.screens.statement import StatementScreen
from src.atm.ui.screens.transfer import TransferScreen
from src.atm.ui.screens.welcome import WelcomeScreen
from src.atm.ui.screens.withdrawal import WithdrawalScreen

__all__ = [
    "DepositScreen",
    "MainMenuScreen",
    "PinEntryScreen",
    "StatementScreen",
    "TransferScreen",
    "WelcomeScreen",
    "WithdrawalScreen",
]
