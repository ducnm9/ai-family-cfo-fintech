"""Financial Strategy Engine — Recommend high-level financial strategies."""

from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow
from intelligence.risk_engine import assess_risk
from intelligence.resilience_engine import assess_resilience
from simulation.debt_engine import optimize_debt_payoff, compare_strategies, DebtStrategy


class Strategy:
    DEBT_FIRST = "debt_first"
    BALANCED_GROWTH = "balanced_growth"
    AGGRESSIVE_SAVING = "aggressive_saving"
    INVESTMENT_FOCUS = "investment_focus"


def recommend_strategy(profile: HouseholdProfile) -> dict:
    """Analyze financial state and recommend the optimal high-level strategy."""

    cf = simulate_cashflow(profile)
    risk = assess_risk(profile)
    resilience = assess_resilience(profile)

    buffer = cf["monthly_buffer"]
    debt_ratio = risk["metrics"]["debt_ratio"]
    stress = cf.get("stress_index", 0)
    emergency_months = resilience["resilience_months"]
    high_interest = [d for d in profile.debts if d.interest_rate > 15]
    total_debt = cf["total_debt_balance"]

    strategies = []

    # Evaluate each strategy
    # 1. Debt First
    debt_score = 0
    debt_reason = []
    if high_interest:
        debt_score += 40
        debt_reason.append("High-interest debt detected")
    if debt_ratio > 30:
        debt_score += 30
        debt_reason.append(f"Debt ratio is {debt_ratio}%")
    if total_debt > 0:
        debt_score += 10
        payoff = optimize_debt_payoff(list(profile.debts), max(buffer * 0.5, 0), DebtStrategy.AVALANCHE)
        base = optimize_debt_payoff(list(profile.debts), 0, DebtStrategy.AVALANCHE)
        improvement = f"Debt free {base['total_months'] - payoff['total_months']} months earlier" if base['total_months'] > payoff['total_months'] else "Reduce total interest"
    else:
        improvement = "No debt to pay off"

    strategies.append({
        "strategy": Strategy.DEBT_FIRST,
        "score": debt_score,
        "reason": "; ".join(debt_reason) if debt_reason else "Low debt levels",
        "expected_improvement": improvement,
    })

    # 2. Balanced Growth
    balanced_score = 30  # baseline
    balanced_reason = []
    if 0.3 <= stress <= 0.6:
        balanced_score += 20
        balanced_reason.append("Moderate stress level suits balanced approach")
    if emergency_months >= 1 and emergency_months < 6:
        balanced_score += 15
        balanced_reason.append("Building emergency fund while managing debt")
    if buffer > 0:
        balanced_score += 10
        balanced_reason.append("Positive cashflow allows diversification")

    strategies.append({
        "strategy": Strategy.BALANCED_GROWTH,
        "score": balanced_score,
        "reason": "; ".join(balanced_reason) if balanced_reason else "General diversification",
        "expected_improvement": "Steady progress on all fronts",
    })

    # 3. Aggressive Saving
    saving_score = 0
    saving_reason = []
    if emergency_months < 3:
        saving_score += 35
        saving_reason.append(f"Emergency fund only {emergency_months} months")
    if stress < 0.5 and buffer > 0:
        saving_score += 20
        saving_reason.append("Low stress allows aggressive saving")
    if total_debt == 0:
        saving_score += 20
        saving_reason.append("No debt — maximize savings")

    strategies.append({
        "strategy": Strategy.AGGRESSIVE_SAVING,
        "score": saving_score,
        "reason": "; ".join(saving_reason) if saving_reason else "Build safety net",
        "expected_improvement": f"Reach 6-month emergency fund in ~{max(1, round((resilience['monthly_essentials'] * 6 - profile.emergency_fund_balance) / max(buffer * 0.6, 1)))} months" if buffer > 0 else "Requires positive cashflow",
    })

    # 4. Investment Focus
    invest_score = 0
    invest_reason = []
    if emergency_months >= 6:
        invest_score += 30
        invest_reason.append("Strong emergency fund allows investing")
    if total_debt == 0 or debt_ratio < 15:
        invest_score += 25
        invest_reason.append("Low debt allows investment focus")
    if cf["savings_rate_pct"] >= 20:
        invest_score += 20
        invest_reason.append(f"High savings rate ({cf['savings_rate_pct']}%) supports investment")

    strategies.append({
        "strategy": Strategy.INVESTMENT_FOCUS,
        "score": invest_score,
        "reason": "; ".join(invest_reason) if invest_reason else "Build long-term wealth",
        "expected_improvement": "Grow wealth through compounding returns",
    })

    # Sort by score
    strategies.sort(key=lambda s: s["score"], reverse=True)
    recommended = strategies[0]

    return {
        "recommended_strategy": recommended["strategy"],
        "reason": recommended["reason"],
        "expected_improvement": recommended["expected_improvement"],
        "all_strategies": strategies,
        "financial_context": {
            "monthly_buffer": round(buffer, 2),
            "debt_ratio": round(debt_ratio, 1),
            "stress_index": round(stress, 3),
            "emergency_months": round(emergency_months, 1),
            "total_debt": round(total_debt, 2),
        },
    }
