from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from models.expense import ExpenseORM
from models.report import MonthlyReportPayload
from services.budget_summary import build_budget_summary, get_month_range_from_str

REPORT_DISCLAIMER = (
    "This report is for personal finance tracking and portfolio demonstration only. "
    "It does not constitute financial or investment advice."
)


def _money(value: Decimal | float | int) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01")))


def build_monthly_report(*, db: Session, user_id: int, month: str) -> MonthlyReportPayload:
    start_date, end_date = get_month_range_from_str(month)
    rows = (
        db.query(ExpenseORM)
        .filter(ExpenseORM.user_id == user_id, ExpenseORM.date >= start_date, ExpenseORM.date < end_date)
        .order_by(ExpenseORM.date.desc(), ExpenseORM.id.desc())
        .all()
    )

    monthly_income = Decimal("0")
    monthly_expense = Decimal("0")
    expense_by_category: dict[str, Decimal] = {}
    recent_transactions: list[dict] = []

    for row in rows:
        amount = Decimal(str(row.amount))
        if row.type == "income":
            monthly_income += amount
        else:
            monthly_expense += amount
            expense_by_category[row.category] = expense_by_category.get(row.category, Decimal("0")) + amount

        recent_transactions.append(
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "category": row.category,
                "type": row.type,
                "amount": _money(amount),
                "note": row.note or "",
            }
        )

    budget_summary = build_budget_summary(db, user_id, month)
    budget_items = [
        {
            "category": item["category"],
            "amount": _money(item["budget"]),
            "used": _money(item["used"]),
            "remaining": _money(item["remaining"]),
            "usagePercent": _money(item["usageRate"]),
            "status": item["status"],
        }
        for item in budget_summary["items"]
    ]

    return MonthlyReportPayload(
        month=month,
        exportedAt=datetime.now(timezone.utc),
        monthlyIncome=_money(monthly_income),
        monthlyExpense=_money(monthly_expense),
        monthlyBalance=_money(monthly_income - monthly_expense),
        expenseByCategory=[
            {"category": category, "amount": _money(amount)}
            for category, amount in sorted(expense_by_category.items(), key=lambda item: (-item[1], item[0]))
        ],
        budgetItems=budget_items,
        recentTransactions=recent_transactions[:10],
        disclaimer=REPORT_DISCLAIMER,
    )


def render_monthly_report_csv(report: MonthlyReportPayload) -> bytes:
    stream = io.StringIO()
    writer = csv.writer(stream)

    writer.writerow(["Monthly Summary"])
    writer.writerow(["Report Month", report.month])
    writer.writerow(["Exported At", report.exportedAt.isoformat()])
    writer.writerow(["Monthly Income", report.monthlyIncome])
    writer.writerow(["Monthly Expense", report.monthlyExpense])
    writer.writerow(["Monthly Balance", report.monthlyBalance])
    writer.writerow([])

    writer.writerow(["Expense By Category"])
    writer.writerow(["Category", "Amount"])
    for item in report.expenseByCategory:
        writer.writerow([item["category"], item["amount"]])
    writer.writerow([])

    writer.writerow(["Budget Status"])
    writer.writerow(["Category", "Amount", "Used", "Remaining", "Usage Percent", "Status"])
    for item in report.budgetItems:
        writer.writerow([item.category, item.amount, item.used, item.remaining, item.usagePercent, item.status])
    writer.writerow([])

    writer.writerow(["Recent Transactions"])
    writer.writerow(["Date", "Category", "Type", "Amount", "Note"])
    for item in report.recentTransactions:
        writer.writerow([item.date, item.category, item.type, item.amount, item.note])
    writer.writerow([])
    writer.writerow(["Disclaimer", report.disclaimer])

    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def render_monthly_report_pdf(report: MonthlyReportPayload) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 48
    y = height - 48

    def write_line(text: str, *, font: str = "Helvetica", size: int = 10, gap: int = 14) -> None:
        nonlocal y
        if y < 48:
            pdf.showPage()
            y = height - 48
        pdf.setFont(font, size)
        pdf.drawString(x, y, text[:110])
        y -= gap

    write_line(f"Finance Report {report.month}", font="Helvetica-Bold", size=16, gap=22)
    write_line(f"Exported At: {report.exportedAt.isoformat()}")
    write_line(f"Monthly Income: {report.monthlyIncome}")
    write_line(f"Monthly Expense: {report.monthlyExpense}")
    write_line(f"Monthly Balance: {report.monthlyBalance}", gap=20)

    write_line("Expense By Category", font="Helvetica-Bold", size=12)
    if report.expenseByCategory:
        for item in report.expenseByCategory:
            write_line(f"- {item['category']}: {item['amount']}")
    else:
        write_line("- No expense data")
    y -= 6

    write_line("Budget Status", font="Helvetica-Bold", size=12)
    if report.budgetItems:
        for item in report.budgetItems:
            write_line(
                f"- {item.category}: amount={item.amount}, used={item.used}, remaining={item.remaining}, "
                f"usage={item.usagePercent}%, status={item.status}"
            )
    else:
        write_line("- No budget data")
    y -= 6

    write_line("Recent Transactions", font="Helvetica-Bold", size=12)
    if report.recentTransactions:
        for item in report.recentTransactions:
            write_line(f"- {item.date} {item.category} {item.type} {item.amount} {item.note}".strip())
    else:
        write_line("- No transactions")

    y -= 12
    write_line(report.disclaimer, font="Helvetica-Oblique", size=9, gap=12)
    pdf.save()
    return buffer.getvalue()
