from models.financial import HouseholdProfile, ExpenseCategory
from simulation.engine import simulate_cashflow


def generate_recommendations(profile: HouseholdProfile) -> list[dict]:
    cashflow = simulate_cashflow(profile)
    recommendations = []
    priority = 1

    # Critical: negative monthly buffer
    if cashflow["monthly_buffer"] < 0:
        recommendations.append({
            "priority": priority,
            "category": "critical",
            "title": "Spending exceeds income",
            "detail": (
                f"You're spending ${abs(cashflow['monthly_buffer']):.2f}/mo more than you earn. "
                "Immediate action needed: reduce expenses or increase income."
            ),
            "impact": "high",
        })
        priority += 1

    # Emergency fund
    if cashflow["emergency_fund_months"] < 1:
        recommendations.append({
            "priority": priority,
            "category": "emergency_fund",
            "title": "Build emergency fund immediately",
            "detail": (
                f"You have {cashflow['emergency_fund_months']:.1f} months of essential expenses saved. "
                "Target at least 3 months, ideally 6 months."
            ),
            "impact": "high",
        })
        priority += 1
    elif cashflow["emergency_fund_months"] < 3:
        recommendations.append({
            "priority": priority,
            "category": "emergency_fund",
            "title": "Grow your emergency fund",
            "detail": (
                f"You have {cashflow['emergency_fund_months']:.1f} months saved. "
                "Work toward 3-6 months of essential expenses."
            ),
            "impact": "medium",
        })
        priority += 1

    # Housing ratio
    if cashflow["housing_ratio_pct"] > 33:
        recommendations.append({
            "priority": priority,
            "category": "housing",
            "title": "Housing costs are high",
            "detail": (
                f"Housing is {cashflow['housing_ratio_pct']:.1f}% of gross income. "
                "The recommended limit is 28-33%. Consider refinancing or downsizing."
            ),
            "impact": "high" if cashflow["housing_ratio_pct"] > 40 else "medium",
        })
        priority += 1

    # Debt-to-income
    if cashflow["debt_to_income_pct"] > 36:
        recommendations.append({
            "priority": priority,
            "category": "debt",
            "title": "Debt-to-income ratio is high",
            "detail": (
                f"Debt payments are {cashflow['debt_to_income_pct']:.1f}% of gross income. "
                "Consider debt consolidation or the avalanche method to pay down faster."
            ),
            "impact": "high",
        })
        priority += 1

    # High-interest debt
    high_interest = [d for d in profile.debts if d.interest_rate > 15]
    if high_interest:
        total_high = sum(d.balance for d in high_interest)
        recommendations.append({
            "priority": priority,
            "category": "debt",
            "title": "Tackle high-interest debt",
            "detail": (
                f"You have ${total_high:,.2f} in debt above 15% APR. "
                "Prioritize paying these off first using the avalanche strategy."
            ),
            "impact": "high",
        })
        priority += 1

    # Savings rate
    if cashflow["savings_rate_pct"] < 10 and cashflow["monthly_buffer"] > 0:
        recommendations.append({
            "priority": priority,
            "category": "savings",
            "title": "Increase savings rate",
            "detail": (
                f"Your savings rate is {cashflow['savings_rate_pct']:.1f}%. "
                "Aim for at least 15-20% for long-term financial security."
            ),
            "impact": "medium",
        })
        priority += 1

    # Variable expense optimization
    if cashflow["variable_expenses"] > cashflow["net_income"] * 0.3:
        recommendations.append({
            "priority": priority,
            "category": "expenses",
            "title": "Review variable spending",
            "detail": (
                f"Variable expenses are ${cashflow['variable_expenses']:,.2f}/mo. "
                "Look for areas to cut in entertainment, dining, and personal spending."
            ),
            "impact": "medium",
        })
        priority += 1

    # Positive reinforcement
    score = cashflow["health_score"]["total_score"]
    if score >= 80:
        recommendations.append({
            "priority": 99,
            "category": "positive",
            "title": "Great financial health!",
            "detail": (
                f"Your financial health score is {score}/100 (Grade: {cashflow['health_score']['grade']}). "
                "Keep up the good work and consider investing your surplus."
            ),
            "impact": "info",
        })

    return sorted(recommendations, key=lambda r: r["priority"])
