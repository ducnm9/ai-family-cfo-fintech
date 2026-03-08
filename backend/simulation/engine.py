from models.financial import HouseholdProfile, ExpenseCategory


def normalize_to_monthly(amount: float, frequency: str) -> float:
    multipliers = {
        "monthly": 1,
        "biweekly": 26 / 12,
        "weekly": 52 / 12,
        "annual": 1 / 12,
    }
    return amount * multipliers.get(frequency, 1)


def simulate_cashflow(profile: HouseholdProfile) -> dict:
    gross_income = sum(
        normalize_to_monthly(i.amount, i.frequency)
        for i in profile.income
    )
    taxable_income = sum(
        normalize_to_monthly(i.amount, i.frequency)
        for i in profile.income
        if i.is_taxable
    )
    estimated_tax = taxable_income * (profile.tax_rate / 100)
    net_income = gross_income - estimated_tax

    total_expenses = sum(e.amount for e in profile.expenses)
    fixed_expenses = sum(e.amount for e in profile.expenses if e.is_fixed)
    variable_expenses = total_expenses - fixed_expenses

    total_debt_payments = sum(d.minimum_payment for d in profile.debts)
    total_debt_balance = sum(d.balance for d in profile.debts)

    monthly_buffer = net_income - total_expenses - total_debt_payments

    savings_rate = (monthly_buffer / net_income * 100) if net_income > 0 else 0
    debt_to_income = (total_debt_payments / gross_income * 100) if gross_income > 0 else 0

    housing_expenses = sum(
        e.amount for e in profile.expenses
        if e.category == ExpenseCategory.HOUSING
    )
    housing_ratio = (housing_expenses / gross_income * 100) if gross_income > 0 else 0

    monthly_essential = sum(
        e.amount for e in profile.expenses
        if e.category in {
            ExpenseCategory.HOUSING, ExpenseCategory.FOOD,
            ExpenseCategory.UTILITIES, ExpenseCategory.INSURANCE,
            ExpenseCategory.HEALTHCARE, ExpenseCategory.TRANSPORTATION,
        }
    ) + total_debt_payments
    emergency_fund_months = (
        profile.emergency_fund_balance / monthly_essential
        if monthly_essential > 0 else 0
    )

    return {
        "gross_income": round(gross_income, 2),
        "estimated_tax": round(estimated_tax, 2),
        "net_income": round(net_income, 2),
        "total_expenses": round(total_expenses, 2),
        "fixed_expenses": round(fixed_expenses, 2),
        "variable_expenses": round(variable_expenses, 2),
        "total_debt_payments": round(total_debt_payments, 2),
        "total_debt_balance": round(total_debt_balance, 2),
        "monthly_buffer": round(monthly_buffer, 2),
        "savings_rate_pct": round(savings_rate, 1),
        "debt_to_income_pct": round(debt_to_income, 1),
        "housing_ratio_pct": round(housing_ratio, 1),
        "emergency_fund_months": round(emergency_fund_months, 1),
        "expense_breakdown": compute_expense_breakdown(profile),
        "health_score": compute_health_score(
            savings_rate, debt_to_income, housing_ratio, emergency_fund_months
        ),
    }


def compute_expense_breakdown(profile: HouseholdProfile) -> dict:
    breakdown = {}
    for e in profile.expenses:
        cat = e.category.value
        breakdown[cat] = round(breakdown.get(cat, 0) + e.amount, 2)
    return breakdown


def compute_health_score(
    savings_rate: float,
    debt_to_income: float,
    housing_ratio: float,
    emergency_months: float,
) -> dict:
    score = 0
    max_score = 100
    details = {}

    # Savings rate (0-25 points): 20%+ is excellent
    if savings_rate >= 20:
        pts = 25
    elif savings_rate >= 10:
        pts = 20
    elif savings_rate >= 5:
        pts = 12
    elif savings_rate > 0:
        pts = 5
    else:
        pts = 0
    score += pts
    details["savings"] = {"score": pts, "max": 25, "value": round(savings_rate, 1)}

    # Debt-to-income (0-25 points): <15% is excellent
    if debt_to_income <= 15:
        pts = 25
    elif debt_to_income <= 25:
        pts = 20
    elif debt_to_income <= 36:
        pts = 12
    elif debt_to_income <= 50:
        pts = 5
    else:
        pts = 0
    score += pts
    details["debt"] = {"score": pts, "max": 25, "value": round(debt_to_income, 1)}

    # Housing ratio (0-25 points): <28% is excellent
    if housing_ratio <= 28:
        pts = 25
    elif housing_ratio <= 33:
        pts = 18
    elif housing_ratio <= 40:
        pts = 10
    else:
        pts = 0
    score += pts
    details["housing"] = {"score": pts, "max": 25, "value": round(housing_ratio, 1)}

    # Emergency fund (0-25 points): 6+ months is excellent
    if emergency_months >= 6:
        pts = 25
    elif emergency_months >= 3:
        pts = 18
    elif emergency_months >= 1:
        pts = 10
    else:
        pts = 0
    score += pts
    details["emergency_fund"] = {"score": pts, "max": 25, "value": round(emergency_months, 1)}

    if score >= 80:
        grade = "A"
    elif score >= 60:
        grade = "B"
    elif score >= 40:
        grade = "C"
    elif score >= 20:
        grade = "D"
    else:
        grade = "F"

    return {"total_score": score, "max_score": max_score, "grade": grade, "details": details}


def project_forward(profile: HouseholdProfile, months: int = 12) -> list[dict]:
    cashflow = simulate_cashflow(profile)
    monthly_buffer = cashflow["monthly_buffer"]
    emergency = profile.emergency_fund_balance
    projections = []

    for month in range(1, months + 1):
        emergency += max(monthly_buffer, 0)
        projections.append({
            "month": month,
            "projected_savings": round(emergency, 2),
            "monthly_buffer": round(monthly_buffer, 2),
        })

    return projections
