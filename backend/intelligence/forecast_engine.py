"""Forecast Engine — Predict future income and expenses using historical snapshots."""

import json
from typing import Optional


def forecast_from_history(snapshots: list[dict], months_ahead: int = 12) -> dict:
    """
    Simple statistical forecast based on monthly snapshot history.
    Uses moving average of last 6 months (or all available).
    """
    if not snapshots:
        return {
            "has_history": False,
            "message": "No historical data available. Close at least 2 months to enable forecasting.",
            "projections": [],
        }

    # Extract monthly summaries
    history = []
    for snap in sorted(snapshots, key=lambda s: s.get("month", "")):
        summary = snap.get("summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)
        history.append({
            "month": snap["month"],
            "income": summary.get("total_income", 0),
            "expenses": summary.get("total_expenses", 0),
            "debt_balance": summary.get("total_debt_balance", 0),
            "buffer": summary.get("monthly_buffer", 0),
        })

    if len(history) < 2:
        return {
            "has_history": True,
            "message": "Need at least 2 months of history for forecasting.",
            "history": history,
            "projections": [],
        }

    # Use last 6 months (or all available)
    window = history[-6:]
    n = len(window)

    avg_income = sum(h["income"] for h in window) / n
    avg_expenses = sum(h["expenses"] for h in window) / n
    avg_buffer = sum(h["buffer"] for h in window) / n

    # Trend detection (simple linear)
    if n >= 3:
        income_trend = (window[-1]["income"] - window[0]["income"]) / (n - 1)
        expense_trend = (window[-1]["expenses"] - window[0]["expenses"]) / (n - 1)
    else:
        income_trend = 0
        expense_trend = 0

    # Project forward
    projections = []
    last_debt = history[-1]["debt_balance"]
    last_debt_payment = abs(avg_buffer) if avg_buffer < 0 else 0

    for m in range(1, months_ahead + 1):
        proj_income = round(avg_income + income_trend * m, 2)
        proj_expenses = round(avg_expenses + expense_trend * m, 2)
        proj_buffer = round(proj_income * 0.76 - proj_expenses - last_debt_payment, 2)  # approx after tax
        proj_debt = max(0, round(last_debt - last_debt_payment, 2))
        last_debt = proj_debt

        projections.append({
            "month_offset": m,
            "projected_income": proj_income,
            "projected_expenses": proj_expenses,
            "projected_buffer": proj_buffer,
            "projected_debt_balance": proj_debt,
        })

    return {
        "has_history": True,
        "months_analyzed": n,
        "averages": {
            "avg_income": round(avg_income, 2),
            "avg_expenses": round(avg_expenses, 2),
            "avg_buffer": round(avg_buffer, 2),
        },
        "trends": {
            "income_trend_per_month": round(income_trend, 2),
            "expense_trend_per_month": round(expense_trend, 2),
        },
        "history": history,
        "projections": projections,
    }
