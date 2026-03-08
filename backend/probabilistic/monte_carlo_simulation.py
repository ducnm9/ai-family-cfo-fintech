"""Monte Carlo Simulation — Probabilistic financial outcome modeling."""

import random
from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow, normalize_to_monthly


def run_monte_carlo(
    profile: HouseholdProfile,
    num_simulations: int = 1000,
    months: int = 60,
    income_volatility: float = 0.10,
    expense_volatility: float = 0.15,
    seed: int = 42,
) -> dict:
    """
    Run Monte Carlo simulation to model probabilistic financial outcomes.

    Parameters:
    - num_simulations: number of simulation runs
    - months: projection period in months
    - income_volatility: std dev as fraction of mean income (default 10%)
    - expense_volatility: std dev as fraction of mean expenses (default 15%)
    """
    rng = random.Random(seed)

    base = simulate_cashflow(profile)
    mean_income = base["net_income"]
    mean_expenses = base["total_expenses"]
    mean_debt_payment = base["total_debt_payments"]

    total_debt = base["total_debt_balance"]
    avg_rate = 0
    if profile.debts:
        avg_rate = sum(d.interest_rate for d in profile.debts) / len(profile.debts) / 100 / 12

    results = []

    for _ in range(num_simulations):
        savings = profile.emergency_fund_balance
        debt_remaining = total_debt
        negative_months = 0
        debt_free_month = None

        for m in range(1, months + 1):
            # Random income and expenses
            monthly_income = max(0, rng.gauss(mean_income, mean_income * income_volatility))
            monthly_expenses = max(0, rng.gauss(mean_expenses, mean_expenses * expense_volatility))

            # Debt interest and payment
            interest = debt_remaining * avg_rate
            debt_remaining += interest
            payment = min(mean_debt_payment, debt_remaining)
            debt_remaining = max(0, debt_remaining - payment)

            buffer = monthly_income - monthly_expenses - payment
            savings += buffer

            if buffer < 0:
                negative_months += 1

            if debt_remaining <= 0.01 and debt_free_month is None:
                debt_free_month = m

        results.append({
            "final_savings": round(savings, 2),
            "final_debt": round(debt_remaining, 2),
            "negative_months": negative_months,
            "debt_free_month": debt_free_month,
        })

    # Analyze results
    final_savings = [r["final_savings"] for r in results]
    final_debts = [r["final_debt"] for r in results]
    debt_free_months = [r["debt_free_month"] for r in results if r["debt_free_month"] is not None]

    prob_negative_cashflow = sum(1 for r in results if r["negative_months"] > months * 0.5) / num_simulations
    prob_debt_free = len(debt_free_months) / num_simulations if total_debt > 0 else 1.0
    prob_savings_positive = sum(1 for s in final_savings if s > 0) / num_simulations

    sorted_savings = sorted(final_savings)
    p10 = sorted_savings[int(num_simulations * 0.10)]
    p50 = sorted_savings[int(num_simulations * 0.50)]
    p90 = sorted_savings[int(num_simulations * 0.90)]

    avg_debt_free = round(sum(debt_free_months) / len(debt_free_months)) if debt_free_months else None

    return {
        "simulations": num_simulations,
        "months": months,
        "parameters": {
            "income_volatility": income_volatility,
            "expense_volatility": expense_volatility,
            "mean_income": round(mean_income, 2),
            "mean_expenses": round(mean_expenses, 2),
        },
        "probabilities": {
            "debt_free_within_period": round(prob_debt_free * 100, 1),
            "negative_cashflow_risk": round(prob_negative_cashflow * 100, 1),
            "savings_positive": round(prob_savings_positive * 100, 1),
        },
        "savings_distribution": {
            "p10_pessimistic": round(p10, 2),
            "p50_median": round(p50, 2),
            "p90_optimistic": round(p90, 2),
            "mean": round(sum(final_savings) / num_simulations, 2),
        },
        "debt_payoff": {
            "avg_months_to_debt_free": avg_debt_free,
            "probability_debt_free": round(prob_debt_free * 100, 1),
        },
    }
