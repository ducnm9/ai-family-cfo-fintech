"""Financial Decision Engine — Compare financial decisions with scenario analysis."""

from models.financial import HouseholdProfile, Expense, ExpenseCategory, Debt
from models.v3 import DecisionRequest
from simulation.engine import simulate_cashflow
from simulation.timeline_engine import generate_timelines
from intelligence.risk_engine import assess_risk


def evaluate_decision(profile: HouseholdProfile, request: DecisionRequest) -> dict:
    """
    For each option:
    1. Modify the profile
    2. Run simulation + risk
    3. Compare all outcomes
    """
    results = []

    for option in request.options:
        modified = profile.model_copy(deep=True)

        # Apply option effects
        if option.new_debt > 0:
            modified.debts.append(Debt(
                name=f"Debt: {option.name}",
                balance=option.new_debt,
                interest_rate=7.0,
                minimum_payment=round(option.new_debt * 0.02, 2),
                debt_type="personal",
            ))

        if option.upfront_cost > 0:
            modified.emergency_fund_balance = max(0, modified.emergency_fund_balance - option.upfront_cost)

        if option.new_monthly_expense > 0:
            modified.expenses.append(Expense(
                name=f"Expense: {option.name}",
                amount=option.new_monthly_expense,
                category=ExpenseCategory.OTHER,
                is_fixed=True,
            ))

        if option.new_monthly_income > 0 and modified.income:
            modified.income[0].amount += option.new_monthly_income

        # Run analysis
        cf = simulate_cashflow(modified)
        risk = assess_risk(modified)
        tl = generate_timelines(modified, 60)

        # Find debt-free year
        debt_free_year = None
        if tl["summary"]["debt_free_month"]:
            debt_free_year = 2026 + tl["summary"]["debt_free_month"] // 12

        results.append({
            "option": option.name,
            "description": option.description,
            "monthly_buffer": round(cf["monthly_buffer"], 2),
            "savings_rate_pct": round(cf["savings_rate_pct"], 1),
            "total_debt": round(cf["total_debt_balance"], 2),
            "stress_index": round(cf.get("stress_index", 0), 3),
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "debt_free_year": debt_free_year,
            "final_savings_5yr": round(tl["summary"]["final_savings"], 2),
            "stress_months_5yr": tl["summary"]["stress_months"],
        })

    # Determine best option
    scored = []
    for r in results:
        # Higher buffer, lower risk, higher savings = better
        score = r["monthly_buffer"] * 0.3 + r["final_savings_5yr"] * 0.0001 - r["risk_score"] * 100
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][1]["option"] if scored else None

    return {
        "question": request.question,
        "options": results,
        "recommendation": best,
        "comparison_summary": {
            "best_for_savings": max(results, key=lambda r: r["final_savings_5yr"])["option"],
            "best_for_risk": min(results, key=lambda r: r["risk_score"])["option"],
            "best_for_cashflow": max(results, key=lambda r: r["monthly_buffer"])["option"],
        },
    }
