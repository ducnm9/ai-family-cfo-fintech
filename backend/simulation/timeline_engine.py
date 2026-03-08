"""Timeline Engine — Extended simulation producing month-by-month timelines."""

from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow


def generate_timelines(profile: HouseholdProfile, months: int = 60) -> dict:
    """
    Generate detailed month-by-month timelines for:
    - cashflow_timeline: income, expenses, buffer per month
    - debt_timeline: total debt balance declining over time
    - savings_timeline: emergency fund / savings growth
    - stress_timeline: months where buffer is negative
    """
    cf = simulate_cashflow(profile)
    net_income = cf["net_income"]
    total_expenses = cf["total_expenses"]
    total_debt_payments = cf["total_debt_payments"]
    monthly_buffer = cf["monthly_buffer"]

    # Build debt detail for amortization
    debts = []
    for d in profile.debts:
        debts.append({
            "name": d.name,
            "balance": d.balance,
            "rate": d.interest_rate / 100 / 12,
            "payment": d.minimum_payment,
        })

    cashflow_timeline = []
    debt_timeline = []
    savings_timeline = []
    stress_timeline = []

    savings = profile.emergency_fund_balance

    for m in range(1, months + 1):
        # Debt amortization
        total_debt = 0
        for d in debts:
            if d["balance"] > 0:
                interest = d["balance"] * d["rate"]
                d["balance"] += interest
                payment = min(d["payment"], d["balance"])
                d["balance"] = max(0, d["balance"] - payment)
            total_debt += d["balance"]

        # Savings accumulation
        if monthly_buffer > 0:
            savings += monthly_buffer

        cashflow_timeline.append({
            "month": m,
            "net_income": round(net_income, 2),
            "total_expenses": round(total_expenses, 2),
            "debt_payments": round(total_debt_payments, 2),
            "buffer": round(monthly_buffer, 2),
        })

        debt_timeline.append({
            "month": m,
            "total_debt": round(total_debt, 2),
            "debts": {d["name"]: round(d["balance"], 2) for d in debts},
        })

        savings_timeline.append({
            "month": m,
            "total_savings": round(savings, 2),
        })

        # Stress index per month = mandatory / income
        month_stress = ((total_expenses + total_debt_payments) / net_income) if net_income > 0 else 1.0
        is_stress = monthly_buffer < 0 or month_stress > 0.7
        stress_timeline.append({
            "month": m,
            "is_stress": is_stress,
            "stress_index": round(month_stress, 3),
            "buffer": round(monthly_buffer, 2),
        })

    # Find debt-free month
    debt_free_month = None
    for dt in debt_timeline:
        if dt["total_debt"] <= 0.01:
            debt_free_month = dt["month"]
            break

    stress_months = sum(1 for s in stress_timeline if s["is_stress"])

    return {
        "months": months,
        "cashflow_timeline": cashflow_timeline[:60],  # max 5 years detail
        "debt_timeline": debt_timeline[:60],
        "savings_timeline": savings_timeline[:60],
        "stress_timeline": stress_timeline[:60],
        "summary": {
            "debt_free_month": debt_free_month,
            "final_debt": round(sum(d["balance"] for d in debts), 2),
            "final_savings": round(savings, 2),
            "stress_months": stress_months,
        },
    }
