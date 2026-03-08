import copy
from models.financial import Debt, DebtStrategy


def debt_avalanche(debts: list[Debt]) -> list[Debt]:
    return sorted(debts, key=lambda d: d.interest_rate, reverse=True)


def debt_snowball(debts: list[Debt]) -> list[Debt]:
    return sorted(debts, key=lambda d: d.balance)


def optimize_debt_payoff(
    debts: list[Debt],
    extra_monthly_payment: float = 0,
    strategy: DebtStrategy = DebtStrategy.AVALANCHE,
) -> dict:
    if not debts:
        return {"strategy": strategy.value, "total_months": 0, "total_interest": 0, "schedule": []}

    if strategy == DebtStrategy.AVALANCHE:
        ordered = debt_avalanche(debts)
    else:
        ordered = debt_snowball(debts)

    balances = {d.name: d.balance for d in ordered}
    rates = {d.name: d.interest_rate / 100 / 12 for d in ordered}
    minimums = {d.name: d.minimum_payment for d in ordered}

    schedule = []
    total_interest = 0
    month = 0
    max_months = 600  # 50 year cap

    while any(b > 0.01 for b in balances.values()) and month < max_months:
        month += 1
        month_detail = {"month": month, "payments": {}, "balances": {}}

        # Apply interest
        for name in balances:
            if balances[name] > 0:
                interest = balances[name] * rates[name]
                balances[name] += interest
                total_interest += interest

        # Collect freed-up minimums from paid-off debts
        available_extra = extra_monthly_payment
        for name in balances:
            if balances[name] <= 0.01:
                available_extra += minimums[name]

        # Pay minimums first
        for name in balances:
            if balances[name] > 0:
                payment = min(minimums[name], balances[name])
                balances[name] -= payment
                month_detail["payments"][name] = round(payment, 2)

        # Apply extra to priority debt
        for d in ordered:
            if balances[d.name] > 0 and available_extra > 0:
                extra = min(available_extra, balances[d.name])
                balances[d.name] -= extra
                month_detail["payments"][d.name] = round(
                    month_detail["payments"].get(d.name, 0) + extra, 2
                )
                available_extra -= extra
                break  # focus extra on top-priority debt

        month_detail["balances"] = {k: round(v, 2) for k, v in balances.items()}
        schedule.append(month_detail)

    payoff_order = []
    seen = set()
    for entry in schedule:
        for name, bal in entry["balances"].items():
            if bal <= 0.01 and name not in seen:
                payoff_order.append({"name": name, "paid_off_month": entry["month"]})
                seen.add(name)

    return {
        "strategy": strategy.value,
        "total_months": month,
        "total_interest_paid": round(total_interest, 2),
        "payoff_order": payoff_order,
        "monthly_schedule": schedule[:60],  # return first 5 years max
    }


def compare_strategies(debts: list[Debt], extra_monthly_payment: float = 0) -> dict:
    avalanche = optimize_debt_payoff(debts, extra_monthly_payment, DebtStrategy.AVALANCHE)
    snowball = optimize_debt_payoff(debts, extra_monthly_payment, DebtStrategy.SNOWBALL)

    interest_saved = snowball["total_interest_paid"] - avalanche["total_interest_paid"]
    months_diff = snowball["total_months"] - avalanche["total_months"]

    return {
        "avalanche": {
            "total_months": avalanche["total_months"],
            "total_interest_paid": avalanche["total_interest_paid"],
            "payoff_order": avalanche["payoff_order"],
        },
        "snowball": {
            "total_months": snowball["total_months"],
            "total_interest_paid": snowball["total_interest_paid"],
            "payoff_order": snowball["payoff_order"],
        },
        "recommendation": {
            "preferred": "avalanche" if interest_saved >= 0 else "snowball",
            "interest_saved_by_avalanche": round(interest_saved, 2),
            "months_faster_by_avalanche": months_diff,
        },
    }
