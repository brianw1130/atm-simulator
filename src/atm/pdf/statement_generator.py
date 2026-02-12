"""PDF statement generator using ReportLab.

Owner: Backend Engineer + UX Designer (layout)
Coverage requirement: 95%+

Generates professional account statements with:
    - Account holder name and masked account number
    - Statement period and generation date
    - Opening and closing balances
    - Transaction table with date, description, amount, and running balance
    - Summary totals (total debits, total credits)
"""

from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _format_cents(cents: int) -> str:
    """Format an integer cents value as a dollar string.

    Args:
        cents: Amount in cents.

    Returns:
        Formatted string, e.g. "$1,234.56".
    """
    dollars = cents / 100
    return f"${dollars:,.2f}"


def generate_statement_pdf(
    file_path: str,
    account_info: dict[str, str],
    transactions: list[dict[str, object]],
    period: str,
    opening_balance_cents: int,
    closing_balance_cents: int,
) -> str:
    """Generate a PDF account statement.

    Creates a formatted PDF containing account information, a transaction
    table with running balances, and summary totals.

    Args:
        file_path: Absolute path where the PDF will be saved.
        account_info: Dict with keys: customer_name, account_number (masked),
            account_type.
        transactions: List of dicts with keys: date (datetime), description (str),
            amount_cents (int), balance_after_cents (int), is_debit (bool).
        period: Human-readable period description (e.g. "Feb 01, 2026 - Feb 11, 2026").
        opening_balance_cents: Balance at the start of the period in cents.
        closing_balance_cents: Balance at the end of the period in cents.

    Returns:
        The file_path where the PDF was saved.
    """
    # Ensure output directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "StatementTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "StatementSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
    )
    info_style = ParagraphStyle(
        "AccountInfo",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
    )

    elements: list[object] = []

    # Header
    elements.append(Paragraph("ATM Simulator", title_style))
    elements.append(Paragraph("Account Statement", subtitle_style))
    elements.append(Spacer(1, 12))

    # Account information
    elements.append(Paragraph(f"<b>Account Holder:</b> {account_info['customer_name']}", info_style))
    elements.append(Paragraph(f"<b>Account Number:</b> {account_info['account_number']}", info_style))
    elements.append(Paragraph(f"<b>Account Type:</b> {account_info['account_type']}", info_style))
    elements.append(Paragraph(f"<b>Statement Period:</b> {period}", info_style))
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")
    elements.append(Paragraph(f"<b>Generated:</b> {generated_at}", info_style))
    elements.append(Spacer(1, 16))

    # Opening balance
    elements.append(
        Paragraph(f"<b>Opening Balance:</b> {_format_cents(opening_balance_cents)}", info_style)
    )
    elements.append(Spacer(1, 12))

    # Transaction table
    table_data: list[list[str]] = [["Date", "Description", "Amount", "Balance"]]

    total_debits_cents = 0
    total_credits_cents = 0

    for txn in transactions:
        txn_date = txn["date"]
        if isinstance(txn_date, datetime):
            date_str = txn_date.strftime("%m/%d/%Y %H:%M")
        else:
            date_str = str(txn_date)

        amount_cents: int = txn["amount_cents"]  # type: ignore[assignment]
        is_debit: bool = txn["is_debit"]  # type: ignore[assignment]
        balance_after_cents: int = txn["balance_after_cents"]  # type: ignore[assignment]

        if is_debit:
            amount_str = f"-{_format_cents(amount_cents)}"
            total_debits_cents += amount_cents
        else:
            amount_str = f"+{_format_cents(amount_cents)}"
            total_credits_cents += amount_cents

        table_data.append([
            date_str,
            str(txn["description"]),
            amount_str,
            _format_cents(balance_after_cents),
        ])

    if len(table_data) == 1:
        # No transactions
        table_data.append(["", "No transactions in this period", "", ""])

    col_widths = [1.5 * inch, 3.0 * inch, 1.25 * inch, 1.25 * inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (2, 0), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Summary
    summary_style = ParagraphStyle(
        "Summary",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
    )
    elements.append(Paragraph(f"<b>Total Debits:</b> -{_format_cents(total_debits_cents)}", summary_style))
    elements.append(Paragraph(f"<b>Total Credits:</b> +{_format_cents(total_credits_cents)}", summary_style))
    elements.append(Spacer(1, 8))
    elements.append(
        Paragraph(f"<b>Closing Balance:</b> {_format_cents(closing_balance_cents)}", summary_style)
    )

    doc.build(elements)
    return file_path
