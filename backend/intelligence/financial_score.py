"""Financial Score — Weighted composite score for overall financial health."""

from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow
from intelligence.risk_engine import assess_risk
from intelligence.resilience_engine import assess_resilience


def compute_financial_score(profile: HouseholdProfile, goal_progress: float = 0) -> dict:
    """
    Calculate a weighted financial health score (0-100).

    Weights per FINANCIAL_ALGORITHMS.md:
    - debt_ratio:    30% (lower is better)
    - savings_rate:  25% (higher is better)
    - resilience:    25% (higher is better)
    - goal_progress: 20% (0-1 scale, provided externally)
    """
    cf = simulate_cashflow(profile)
    risk = assess_risk(profile)
    resilience = assess_resilience(profile)

    # Debt ratio score (0-30): lower debt ratio = higher score
    debt_ratio = risk["metrics"]["debt_ratio"]
    if debt_ratio <= 10:
        debt_score = 30
    elif debt_ratio <= 20:
        debt_score = 24
    elif debt_ratio <= 36:
        debt_score = 15
    elif debt_ratio <= 50:
        debt_score = 6
    else:
        debt_score = 0

    # Savings rate score (0-25): higher savings = higher score
    savings_rate = cf["savings_rate_pct"]
    if savings_rate >= 25:
        savings_score = 25
    elif savings_rate >= 15:
        savings_score = 20
    elif savings_rate >= 10:
        savings_score = 15
    elif savings_rate > 0:
        savings_score = 8
    else:
        savings_score = 0

    # Resilience score (0-25): more months = higher score
    res_months = resilience["resilience_months"]
    if res_months >= 6:
        resilience_score = 25
    elif res_months >= 3:
        resilience_score = 18
    elif res_months >= 1:
        resilience_score = 10
    else:
        resilience_score = 0

    # Goal progress score (0-20): 0-1 scale
    goal_score = round(min(1.0, max(0, goal_progress)) * 20)

    total = debt_score + savings_score + resilience_score + goal_score

    if total >= 80:
        grade = "A"
    elif total >= 60:
        grade = "B"
    elif total >= 40:
        grade = "C"
    elif total >= 20:
        grade = "D"
    else:
        grade = "F"

    return {
        "financial_score": total,
        "max_score": 100,
        "grade": grade,
        "breakdown": {
            "debt_ratio": {"score": debt_score, "max": 30, "value": round(debt_ratio, 1)},
            "savings_rate": {"score": savings_score, "max": 25, "value": round(savings_rate, 1)},
            "resilience": {"score": resilience_score, "max": 25, "value": round(res_months, 1)},
            "goal_progress": {"score": goal_score, "max": 20, "value": round(goal_progress * 100, 1)},
        },
        "risk_level": risk["risk_level"],
        "resilience_level": resilience["resilience_level"],
    }
