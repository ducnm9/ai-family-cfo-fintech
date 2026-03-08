import copy
from models.financial import HouseholdProfile, Scenario, ScenarioType, Debt, IncomeSource, Expense, ExpenseCategory
from simulation.engine import simulate_cashflow


def apply_scenario(profile: HouseholdProfile, scenario: Scenario) -> HouseholdProfile:
    modified = profile.model_copy(deep=True)

    stype = scenario.type

    if stype == ScenarioType.INCOME_INCREASE:
        if scenario.target_name:
            for inc in modified.income:
                if inc.name == scenario.target_name:
                    inc.amount += scenario.amount
                    break
        elif modified.income:
            modified.income[0].amount += scenario.amount

    elif stype == ScenarioType.INCOME_DECREASE:
        if scenario.target_name:
            for inc in modified.income:
                if inc.name == scenario.target_name:
                    inc.amount = max(0, inc.amount - scenario.amount)
                    break
        elif modified.income:
            modified.income[0].amount = max(0, modified.income[0].amount - scenario.amount)

    elif stype == ScenarioType.EXPENSE_INCREASE:
        modified.expenses.append(Expense(
            name=scenario.description or "New expense",
            amount=scenario.amount,
            category=ExpenseCategory.OTHER,
            is_fixed=True,
        ))

    elif stype == ScenarioType.EXPENSE_DECREASE:
        if scenario.target_name:
            for exp in modified.expenses:
                if exp.name == scenario.target_name:
                    exp.amount = max(0, exp.amount - scenario.amount)
                    break
        else:
            remaining = scenario.amount
            for exp in sorted(modified.expenses, key=lambda e: e.amount, reverse=True):
                if not exp.is_fixed and remaining > 0:
                    reduction = min(exp.amount, remaining)
                    exp.amount -= reduction
                    remaining -= reduction

    elif stype == ScenarioType.NEW_DEBT:
        modified.debts.append(Debt(
            name=scenario.description or "New debt",
            balance=scenario.amount,
            interest_rate=7.0,
            minimum_payment=round(scenario.amount * 0.02, 2),
        ))

    elif stype == ScenarioType.EXTRA_DEBT_PAYMENT:
        if scenario.target_name:
            for debt in modified.debts:
                if debt.name == scenario.target_name:
                    debt.minimum_payment += scenario.amount
                    break
        elif modified.debts:
            highest = max(modified.debts, key=lambda d: d.interest_rate)
            highest.minimum_payment += scenario.amount

    elif stype == ScenarioType.JOB_LOSS:
        if scenario.target_name:
            modified.income = [i for i in modified.income if i.name != scenario.target_name]
        elif modified.income:
            modified.income.pop(0)

    elif stype == ScenarioType.EMERGENCY:
        modified.emergency_fund_balance = max(
            0, modified.emergency_fund_balance - scenario.amount
        )

    elif stype == ScenarioType.INVESTMENT_RETURN:
        monthly_return = scenario.amount / 12
        modified.income.append(IncomeSource(
            name="Investment returns",
            amount=monthly_return,
            frequency="monthly",
            is_taxable=True,
        ))

    return modified


def run_scenario_comparison(
    profile: HouseholdProfile,
    scenarios: list[Scenario],
) -> dict:
    baseline = simulate_cashflow(profile)
    results = [{"name": "baseline", "scenario": None, "result": baseline}]

    for scenario in scenarios:
        modified_profile = apply_scenario(profile, scenario)
        result = simulate_cashflow(modified_profile)

        diff = {
            "monthly_buffer_change": round(
                result["monthly_buffer"] - baseline["monthly_buffer"], 2
            ),
            "savings_rate_change": round(
                result["savings_rate_pct"] - baseline["savings_rate_pct"], 1
            ),
            "health_score_change": (
                result["health_score"]["total_score"] - baseline["health_score"]["total_score"]
            ),
        }

        results.append({
            "name": scenario.description or scenario.type.value,
            "scenario": scenario.model_dump(),
            "result": result,
            "diff_from_baseline": diff,
        })

    return {"baseline": baseline, "scenarios": results[1:]}


def stress_test(profile: HouseholdProfile) -> dict:
    tests = [
        Scenario(type=ScenarioType.JOB_LOSS, description="Primary income loss"),
        Scenario(type=ScenarioType.EMERGENCY, amount=5000, description="$5k emergency"),
        Scenario(type=ScenarioType.EMERGENCY, amount=10000, description="$10k emergency"),
        Scenario(type=ScenarioType.EXPENSE_INCREASE, amount=500, description="Expenses +$500/mo"),
        Scenario(type=ScenarioType.INCOME_DECREASE, amount=1000, description="Income -$1000/mo"),
    ]
    return run_scenario_comparison(profile, tests)
