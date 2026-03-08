"""V2 Recommendation Engine — AI-powered recommendations using all intelligence modules."""

from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow
from intelligence.risk_engine import assess_risk
from intelligence.resilience_engine import assess_resilience
from intelligence.financial_score import compute_financial_score
from optimization.allocation_optimizer import optimize_allocation


def generate_v2_recommendations(
    profile: HouseholdProfile,
    snapshots: list[dict] = None,
) -> dict:
    """
    Comprehensive recommendation engine.
    Workflow:
    1. Run simulation
    2. Run risk engine
    3. Run optimization engine
    4. Generate prioritized recommendations
    """
    cashflow = simulate_cashflow(profile)
    risk = assess_risk(profile)
    resilience = assess_resilience(profile)
    score = compute_financial_score(profile)
    allocation = optimize_allocation(profile)

    recommendations = []
    priority = 1

    # Critical: negative cashflow
    if cashflow["monthly_buffer"] < 0:
        deficit = abs(cashflow["monthly_buffer"])
        recommendations.append({
            "priority": priority,
            "category": "critical",
            "title": "Monthly deficit detected",
            "detail": (
                f"You're spending {deficit:,.0f}/mo more than you earn. "
                "Immediate action: cut variable expenses or increase income."
            ),
            "impact": "high",
            "action_type": "reduce_expenses",
        })
        priority += 1

    # Risk-based recommendations
    for flag in risk["flags"]:
        if flag["flag"] == "HIGH_DEBT_RATIO" and flag["severity"] in ("critical", "high"):
            recommendations.append({
                "priority": priority,
                "category": "debt",
                "title": f"Debt ratio is {flag['severity']}: {flag['value']}%",
                "detail": (
                    f"Debt payments consume {flag['value']}% of income (threshold: {flag['threshold']}%). "
                    "Consider debt consolidation or the avalanche payoff method."
                ),
                "impact": "high",
                "action_type": "reduce_debt",
            })
            priority += 1

        elif flag["flag"] == "LOW_EMERGENCY_FUND":
            months = flag["value"]
            recommendations.append({
                "priority": priority,
                "category": "emergency_fund",
                "title": f"Emergency fund: {months} months" if months > 0 else "No emergency fund",
                "detail": (
                    f"You have {months} months of essential expenses saved. "
                    "Target at least 3 months, ideally 6 months."
                ),
                "impact": "high" if months < 1 else "medium",
                "action_type": "build_emergency_fund",
            })
            priority += 1

        elif flag["flag"] == "HIGH_INTEREST_DEBT":
            recommendations.append({
                "priority": priority,
                "category": "debt",
                "title": f"High-interest debt: {flag['value']:,.0f}",
                "detail": (
                    f"You have {flag['value']:,.0f} in debt above 15% APR. "
                    "Prioritize these using the avalanche strategy to minimize total interest."
                ),
                "impact": "high",
                "action_type": "reduce_debt",
            })
            priority += 1

    # Allocation-based recommendations
    if allocation["has_surplus"] and allocation["allocations"]:
        alloc_summary = []
        for a in allocation["allocations"][:3]:
            alloc_summary.append(f"{a['target'].replace('_', ' ').title()}: {a['amount']:,.0f}/mo")

        recommendations.append({
            "priority": priority,
            "category": "optimization",
            "title": "Suggested surplus allocation",
            "detail": "Optimal distribution of your monthly surplus: " + " | ".join(alloc_summary),
            "impact": "medium",
            "action_type": "optimize_allocation",
        })
        priority += 1

        if allocation["payoff_impact"] and allocation["payoff_impact"]["months_saved"] > 0:
            pi = allocation["payoff_impact"]
            recommendations.append({
                "priority": priority,
                "category": "optimization",
                "title": f"Debt-free {pi['months_saved']} months earlier",
                "detail": (
                    f"By allocating extra to debt, pay off in {pi['optimized_months']} months "
                    f"instead of {pi['base_months']} months. Save {pi['interest_saved']:,.0f} in interest."
                ),
                "impact": "medium",
                "action_type": "accelerate_debt",
            })
            priority += 1

    # Resilience recommendation
    if resilience["resilience_months"] < 3:
        recommendations.append({
            "priority": priority,
            "category": "resilience",
            "title": f"Financial resilience: {resilience['resilience_level']}",
            "detail": (
                f"You can survive {resilience['resilience_months']} months without income. "
                f"Monthly essentials: {resilience['monthly_essentials']:,.0f}. Build your safety net."
            ),
            "impact": "medium",
            "action_type": "build_resilience",
        })
        priority += 1

    # Positive reinforcement
    if score["financial_score"] >= 70:
        recommendations.append({
            "priority": 99,
            "category": "positive",
            "title": f"Strong financial health — Score: {score['financial_score']}/100",
            "detail": (
                f"Grade: {score['grade']}. "
                "Your finances are well-managed. Consider investing surplus for growth."
            ),
            "impact": "info",
            "action_type": "maintain",
        })

    return {
        "financial_score": score,
        "risk_assessment": risk,
        "resilience": {
            "months": resilience["resilience_months"],
            "level": resilience["resilience_level"],
        },
        "allocation": allocation,
        "recommendations": sorted(recommendations, key=lambda r: r["priority"]),
    }
