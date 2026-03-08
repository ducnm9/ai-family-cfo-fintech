"""Resilience Engine — Measure how many months the household can survive without income."""

from models.financial import HouseholdProfile, ExpenseCategory


def assess_resilience(profile: HouseholdProfile) -> dict:
    """
    Calculate resilience metrics: how long savings last without any income.
    """
    # Monthly essential expenses (must-pay)
    essential_expenses = sum(
        e.amount for e in profile.expenses
        if e.category in {
            ExpenseCategory.HOUSING, ExpenseCategory.FOOD,
            ExpenseCategory.UTILITIES, ExpenseCategory.INSURANCE,
            ExpenseCategory.HEALTHCARE, ExpenseCategory.TRANSPORTATION,
        }
    )
    debt_payments = sum(d.minimum_payment for d in profile.debts)
    total_essentials = essential_expenses + debt_payments

    # All expenses
    total_expenses = sum(e.amount for e in profile.expenses) + debt_payments

    savings = profile.emergency_fund_balance

    # Resilience with essential-only spending
    essential_months = (savings / total_essentials) if total_essentials > 0 else 999
    # Resilience with all current spending
    full_months = (savings / total_expenses) if total_expenses > 0 else 999

    # Month-by-month survival simulation (with essentials only)
    survival_timeline = []
    remaining = savings
    for month in range(1, 25):  # up to 2 years
        remaining -= total_essentials
        if remaining < 0:
            survival_timeline.append({"month": month, "remaining": 0, "status": "depleted"})
            break
        survival_timeline.append({
            "month": month,
            "remaining": round(remaining, 2),
            "status": "ok" if remaining > total_essentials else "warning",
        })

    if essential_months >= 6:
        level = "strong"
    elif essential_months >= 3:
        level = "moderate"
    elif essential_months >= 1:
        level = "weak"
    else:
        level = "critical"

    return {
        "resilience_months": round(essential_months, 1),
        "resilience_months_full_spending": round(full_months, 1),
        "resilience_level": level,
        "savings": round(savings, 2),
        "monthly_essentials": round(total_essentials, 2),
        "monthly_total": round(total_expenses, 2),
        "survival_timeline": survival_timeline,
    }
