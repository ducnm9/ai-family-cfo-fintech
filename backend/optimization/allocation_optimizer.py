"""Allocation Optimizer — Optimize income distribution between debt, savings, and expenses."""

from models.financial import HouseholdProfile
from simulation.engine import simulate_cashflow
from simulation.debt_engine import optimize_debt_payoff, DebtStrategy


def optimize_allocation(profile: HouseholdProfile) -> dict:
    """
    Optimize allocation of surplus income between:
    - Extra debt payments (minimize interest)
    - Emergency fund (build safety net)
    - Savings goals

    Objective: minimize total interest, maximize savings, minimize financial stress.
    """
    cf = simulate_cashflow(profile)
    monthly_buffer = cf["monthly_buffer"]
    emergency_months = cf["emergency_fund_months"]

    if monthly_buffer <= 0:
        variable = cf["variable_expenses"]
        return {
            "has_surplus": False,
            "monthly_buffer": round(monthly_buffer, 2),
            "message": "No surplus to allocate. Focus on reducing expenses or increasing income.",
            "allocations": [],
            "payoff_impact": None,
            "reasoning": ["Negative cashflow — reduce expenses first"],
            "recommended_debt_payment": round(cf["total_debt_payments"], 2),
            "recommended_savings_rate": 0,
            "recommended_expense_reduction": round(abs(monthly_buffer) + variable * 0.1, 2),
        }

    surplus = monthly_buffer
    allocations = []
    reasoning = []

    # Priority 1: Emergency fund to 1 month (if below)
    essential_monthly = cf["total_expenses"] + cf["total_debt_payments"]
    if emergency_months < 1 and essential_monthly > 0:
        needed = essential_monthly - profile.emergency_fund_balance
        emergency_alloc = min(surplus, max(0, needed))
        if emergency_alloc > 0:
            allocations.append({
                "target": "emergency_fund",
                "amount": round(emergency_alloc, 2),
                "priority": 1,
                "reason": "Build minimum 1-month emergency fund first",
            })
            surplus -= emergency_alloc
            reasoning.append("Emergency fund is critically low")

    # Priority 2: High-interest debt (>15% APR)
    high_interest = [d for d in profile.debts if d.interest_rate > 15]
    if high_interest and surplus > 0:
        # Allocate up to 60% of remaining surplus to high-interest debt
        debt_alloc = min(surplus * 0.6, surplus)
        if debt_alloc > 10:
            allocations.append({
                "target": "high_interest_debt",
                "amount": round(debt_alloc, 2),
                "priority": 2,
                "reason": f"Pay down {len(high_interest)} high-interest debt(s) to reduce interest costs",
            })
            surplus -= debt_alloc
            reasoning.append("High-interest debt detected")

    # Priority 3: Emergency fund to 3 months
    if emergency_months < 3 and surplus > 0:
        needed_3mo = essential_monthly * 3 - profile.emergency_fund_balance
        emergency_alloc_2 = min(surplus * 0.5, max(0, needed_3mo))
        if emergency_alloc_2 > 0:
            allocations.append({
                "target": "emergency_fund",
                "amount": round(emergency_alloc_2, 2),
                "priority": 3,
                "reason": "Grow emergency fund toward 3-month target",
            })
            surplus -= emergency_alloc_2

    # Priority 4: Remaining debt
    other_debts = [d for d in profile.debts if d.interest_rate <= 15 and d.balance > 0]
    if other_debts and surplus > 0:
        debt_alloc_2 = min(surplus * 0.4, surplus)
        if debt_alloc_2 > 10:
            allocations.append({
                "target": "other_debt",
                "amount": round(debt_alloc_2, 2),
                "priority": 4,
                "reason": "Accelerate remaining debt payoff",
            })
            surplus -= debt_alloc_2

    # Priority 5: Savings/investment
    if surplus > 0:
        allocations.append({
            "target": "savings_investment",
            "amount": round(surplus, 2),
            "priority": 5,
            "reason": "Invest or save for long-term goals",
        })

    # Impact projection: how much earlier debts are paid off with extra allocation
    total_extra_to_debt = sum(a["amount"] for a in allocations if "debt" in a["target"])
    payoff_impact = None
    if profile.debts and total_extra_to_debt > 0:
        base_payoff = optimize_debt_payoff(list(profile.debts), 0, DebtStrategy.AVALANCHE)
        optimized_payoff = optimize_debt_payoff(list(profile.debts), total_extra_to_debt, DebtStrategy.AVALANCHE)
        payoff_impact = {
            "base_months": base_payoff["total_months"],
            "optimized_months": optimized_payoff["total_months"],
            "months_saved": base_payoff["total_months"] - optimized_payoff["total_months"],
            "interest_saved": round(base_payoff["total_interest_paid"] - optimized_payoff["total_interest_paid"], 2),
        }

    # ENGINE_INTERFACES.md Section 5: structured recommendations
    total_to_debt = sum(a["amount"] for a in allocations if "debt" in a["target"])
    total_to_savings = sum(a["amount"] for a in allocations if a["target"] in ("emergency_fund", "savings_investment"))
    recommended_savings_rate = round((total_to_savings / cf["net_income"] * 100) if cf["net_income"] > 0 else 0, 1)

    # Expense reduction recommendation: if buffer is negative or stress is high
    stress_index = cf.get("stress_index", 0)
    recommended_expense_reduction = 0
    if cf["monthly_buffer"] <= 0:
        recommended_expense_reduction = round(abs(cf["monthly_buffer"]) * 1.1, 2)  # 10% more than deficit
    elif stress_index > 0.7 and cf["variable_expenses"] > 0:
        recommended_expense_reduction = round(cf["variable_expenses"] * 0.15, 2)  # cut 15% discretionary

    return {
        "has_surplus": True,
        "monthly_buffer": round(cf["monthly_buffer"], 2),
        "allocations": allocations,
        "total_allocated": round(sum(a["amount"] for a in allocations), 2),
        "payoff_impact": payoff_impact,
        "reasoning": reasoning,
        # ENGINE_INTERFACES.md compliant fields
        "recommended_debt_payment": round(total_to_debt + cf["total_debt_payments"], 2),
        "recommended_savings_rate": recommended_savings_rate,
        "recommended_expense_reduction": recommended_expense_reduction,
    }
