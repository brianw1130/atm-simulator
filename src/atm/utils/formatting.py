"""Display formatting utilities for currency, account numbers, and dates.

Owner: Backend Engineer
Coverage requirement: 100%

Functions:
    - format_currency(cents) -> str: Format cents as dollar string (e.g., "$1,234.56")
    - mask_account_number(account_number) -> str: Mask all but last 4 chars
    - format_transaction_date(dt) -> str: Format datetime for display
    - format_denomination_breakdown(cents) -> dict: Break amount into bill denominations
"""

# TODO: Implement formatting utility functions


def mask_account_number(account_number: str) -> str:
    """Mask all characters except the last 4 with asterisks, preserving hyphens.

    Examples:
        >>> mask_account_number("1000-0001-0001")
        '****-****-0001'
        >>> mask_account_number("12345678")
        '****5678'
        >>> mask_account_number("AB")
        'AB'

    Args:
        account_number: The account number string to mask.

    Returns:
        The masked account number. If the string (excluding hyphens)
        has 4 or fewer characters, it is returned unchanged.
    """
    if not account_number:
        return account_number

    non_hyphen_chars = [c for c in account_number if c != "-"]
    if len(non_hyphen_chars) <= 4:
        return account_number

    chars_to_mask = len(non_hyphen_chars) - 4
    masked_count = 0
    result: list[str] = []
    for char in account_number:
        if char == "-":
            result.append("-")
        elif masked_count < chars_to_mask:
            result.append("*")
            masked_count += 1
        else:
            result.append(char)
    return "".join(result)
