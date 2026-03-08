"""Life Planning Engine — Simulate major life events and their financial impact."""

from models.financial import HouseholdProfile, Expense, ExpenseCategory, Debt
from models.v3 import LifeEventInput, LifeEventType
from simulation.engine import simulate_cashflow


def simulate_life_event(profile: HouseholdProfile, event: LifeEventInput) -> dict:
    """
    1. Modify financial state based on life event
    2. Inject new expense or debt
    3. Rerun simulation engine
    4. Compare baseline vs scenario
    """
    baseline = simulate_cashflow(profile)
    modified = profile.model_copy(deep=True)

    event_details = {}

    if event.event == LifeEventType.BUY_HOUSE:
        loan = event.price - event.down_payment
        monthly_rate = event.mortgage_rate / 12
        n_payments = event.mortgage_years * 12
        if monthly_rate > 0 and n_payments > 0:
            monthly_payment = loan * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
        else:
            monthly_payment = loan / max(n_payments, 1)

        modified.debts.append(Debt(
            name="Mortgage",
            balance=round(loan, 2),
            interest_rate=round(event.mortgage_rate * 100, 2),
            minimum_payment=round(monthly_payment, 2),
            debt_type="mortgage",
        ))
        modified.emergency_fund_balance = max(0, modified.emergency_fund_balance - event.down_payment)
        event_details = {
            "loan_amount": round(loan, 2),
            "monthly_payment": round(monthly_payment, 2),
            "total_cost": round(monthly_payment * n_payments, 2),
            "total_interest": round(monthly_payment * n_payments - loan, 2),
        }

    elif event.event == LifeEventType.HAVE_CHILD:
        monthly_cost = event.new_monthly_expense or 3000000  # default childcare cost
        modified.expenses.append(Expense(
            name="Childcare & baby expenses",
            amount=monthly_cost,
            category=ExpenseCategory.CHILDCARE,
            is_fixed=True,
        ))
        event_details = {"monthly_cost": monthly_cost}

    elif event.event == LifeEventType.CAREER_CHANGE:
        if event.income_loss_months > 0:
            # Simulate gap period impact on savings
            gap_cost = baseline["net_income"] * event.income_loss_months
            modified.emergency_fund_balance = max(0, modified.emergency_fund_balance - gap_cost)
            event_details["gap_cost"] = round(gap_cost, 2)
        if event.new_income > 0 and modified.income:
            modified.income[0].amount = event.new_income
            event_details["new_income"] = event.new_income

    elif event.event == LifeEventType.JOB_LOSS:
        months = event.income_loss_months or 6
        if modified.income:
            lost_income = modified.income[0].amount
            modified.income.pop(0)
            event_details = {
                "lost_income": lost_income,
                "estimated_gap_months": months,
                "savings_burn": round(lost_income * months, 2),
            }

    elif event.event == LifeEventType.START_BUSINESS:
        cost = event.startup_cost or 50000000
        modified.emergency_fund_balance = max(0, modified.emergency_fund_balance - cost)
        if event.new_monthly_expense > 0:
            modified.expenses.append(Expense(
                name="Business expenses",
                amount=event.new_monthly_expense,
                category=ExpenseCategory.OTHER,
                is_fixed=True,
            ))
        event_details = {"startup_cost": cost}

    elif event.event == LifeEventType.RETIREMENT:
        modified.income = []  # no more work income
        monthly_need = event.retirement_monthly_need or baseline["total_expenses"]
        event_details = {
            "monthly_need": round(monthly_need, 2),
            "annual_need": round(monthly_need * 12, 2),
            "years_of_savings": round(modified.emergency_fund_balance / (monthly_need * 12), 1) if monthly_need > 0 else 0,
        }

    scenario = simulate_cashflow(modified)

    return {
        "event": event.event.value,
        "event_details": event_details,
        "baseline": {
            "monthly_buffer": baseline["monthly_buffer"],
            "savings_rate_pct": baseline["savings_rate_pct"],
            "stress_index": baseline.get("stress_index", 0),
        },
        "after_event": {
            "monthly_buffer": scenario["monthly_buffer"],
            "savings_rate_pct": scenario["savings_rate_pct"],
            "stress_index": scenario.get("stress_index", 0),
            "total_debt": scenario["total_debt_balance"],
        },
        "impact": {
            "buffer_change": round(scenario["monthly_buffer"] - baseline["monthly_buffer"], 2),
            "savings_rate_change": round(scenario["savings_rate_pct"] - baseline["savings_rate_pct"], 1),
            "stress_change": round(scenario.get("stress_index", 0) - baseline.get("stress_index", 0), 3),
        },
    }
