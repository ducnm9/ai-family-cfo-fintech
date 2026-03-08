"""Risk Engine — Detect financial risk flags from a household profile."""

from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow


class RiskFlag:
    HIGH_DEBT_RATIO = "HIGH_DEBT_RATIO"
    LOW_EMERGENCY_FUND = "LOW_EMERGENCY_FUND"
    HIGH_EXPENSE_RATIO = "HIGH_EXPENSE_RATIO"
    NEGATIVE_CASHFLOW = "NEGATIVE_CASHFLOW"
    HIGH_INTEREST_DEBT = "HIGH_INTEREST_DEBT"
    SINGLE_INCOME_DEPENDENCY = "SINGLE_INCOME_DEPENDENCY"
    NO_SAVINGS = "NO_SAVINGS"


def assess_risk(profile: HouseholdProfile) -> dict:
    cf = simulate_cashflow(profile)

    gross_income = cf["gross_income"]
    net_income = cf["net_income"]
    total_expenses = cf["total_expenses"]
    total_debt_payments = cf["total_debt_payments"]
    total_debt_balance = cf["total_debt_balance"]
    monthly_buffer = cf["monthly_buffer"]
    emergency_months = cf["emergency_fund_months"]

    flags = []
    risk_score = 0  # 0 = no risk, 100 = extreme risk

    # Debt ratio: debt payments / gross income
    debt_ratio = (total_debt_payments / gross_income * 100) if gross_income > 0 else 0
    if debt_ratio > 50:
        flags.append({"flag": RiskFlag.HIGH_DEBT_RATIO, "severity": "critical", "value": round(debt_ratio, 1), "threshold": 50})
        risk_score += 25
    elif debt_ratio > 36:
        flags.append({"flag": RiskFlag.HIGH_DEBT_RATIO, "severity": "high", "value": round(debt_ratio, 1), "threshold": 36})
        risk_score += 15

    # Expense ratio: total expenses / net income
    expense_ratio = (total_expenses / net_income * 100) if net_income > 0 else 100
    if expense_ratio > 90:
        flags.append({"flag": RiskFlag.HIGH_EXPENSE_RATIO, "severity": "critical", "value": round(expense_ratio, 1), "threshold": 90})
        risk_score += 20
    elif expense_ratio > 75:
        flags.append({"flag": RiskFlag.HIGH_EXPENSE_RATIO, "severity": "high", "value": round(expense_ratio, 1), "threshold": 75})
        risk_score += 10

    # Emergency fund
    if emergency_months < 1:
        flags.append({"flag": RiskFlag.LOW_EMERGENCY_FUND, "severity": "critical", "value": round(emergency_months, 1), "threshold": 1})
        risk_score += 20
    elif emergency_months < 3:
        flags.append({"flag": RiskFlag.LOW_EMERGENCY_FUND, "severity": "high", "value": round(emergency_months, 1), "threshold": 3})
        risk_score += 10

    # Negative cashflow
    if monthly_buffer < 0:
        flags.append({"flag": RiskFlag.NEGATIVE_CASHFLOW, "severity": "critical", "value": round(monthly_buffer, 2), "threshold": 0})
        risk_score += 25

    # High-interest debt (>15% APR)
    high_interest = [d for d in profile.debts if d.interest_rate > 15]
    if high_interest:
        total_high = sum(d.balance for d in high_interest)
        flags.append({"flag": RiskFlag.HIGH_INTEREST_DEBT, "severity": "high", "value": round(total_high, 2), "threshold": 0})
        risk_score += 10

    # Single income dependency
    recurring_income = [i for i in profile.income if getattr(i, "is_recurring", True)]
    if len(recurring_income) <= 1 and gross_income > 0:
        flags.append({"flag": RiskFlag.SINGLE_INCOME_DEPENDENCY, "severity": "medium", "value": len(recurring_income), "threshold": 2})
        risk_score += 5

    # No savings
    if cf["savings_rate_pct"] <= 0:
        flags.append({"flag": RiskFlag.NO_SAVINGS, "severity": "high", "value": round(cf["savings_rate_pct"], 1), "threshold": 0})
        risk_score += 10

    risk_score = min(100, risk_score)

    if risk_score >= 70:
        risk_level = "critical"
    elif risk_score >= 40:
        risk_level = "high"
    elif risk_score >= 20:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": flags,
        "metrics": {
            "debt_ratio": round(debt_ratio, 1),
            "expense_ratio": round(expense_ratio, 1),
            "emergency_months": round(emergency_months, 1),
            "monthly_buffer": round(monthly_buffer, 2),
            "savings_rate": round(cf["savings_rate_pct"], 1),
        },
    }
