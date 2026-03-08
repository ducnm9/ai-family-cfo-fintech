"""Goal Optimization Engine — Compute optimal savings plans for financial goals."""

import math
from models.v3 import FinancialGoal, GoalListRequest


def optimize_goals(request: GoalListRequest) -> dict:
    """
    Minimize time_to_goal subject to income, expenses, debt_payments.
    Allocates monthly surplus across goals by priority.
    """
    goals = sorted(request.goals, key=lambda g: g.priority)
    surplus = request.monthly_surplus

    if surplus <= 0:
        return {
            "feasible": False,
            "message": "No surplus available. Reduce expenses or increase income first.",
            "plans": [],
        }

    plans = []
    remaining_surplus = surplus

    for goal in goals:
        gap = goal.target_amount - goal.current_amount
        if gap <= 0:
            plans.append({
                "goal": goal.name,
                "goal_type": goal.goal_type.value,
                "status": "completed",
                "remaining": 0,
                "monthly_allocation": 0,
                "completion_months": 0,
                "priority": goal.priority,
            })
            continue

        # Allocate proportionally by priority (higher priority = more allocation)
        # Priority 1 gets up to 40%, 2 gets 25%, 3 gets 20%, 4 gets 10%, 5 gets 5%
        priority_weights = {1: 0.40, 2: 0.25, 3: 0.20, 4: 0.10, 5: 0.05}
        weight = priority_weights.get(goal.priority, 0.10)
        allocation = min(remaining_surplus, surplus * weight)
        allocation = max(allocation, 1)  # at least 1

        if allocation > 0:
            months_needed = math.ceil(gap / allocation)
        else:
            months_needed = 999

        # If there's a deadline, check if we need more
        if goal.deadline_months and months_needed > goal.deadline_months:
            required = math.ceil(gap / goal.deadline_months)
            if required <= remaining_surplus:
                allocation = required
                months_needed = goal.deadline_months

        remaining_surplus = max(0, remaining_surplus - allocation)

        plans.append({
            "goal": goal.name,
            "goal_type": goal.goal_type.value,
            "status": "in_progress",
            "remaining": round(gap, 2),
            "monthly_allocation": round(allocation, 2),
            "completion_months": months_needed,
            "completion_years": round(months_needed / 12, 1),
            "priority": goal.priority,
            "on_track": goal.deadline_months is None or months_needed <= goal.deadline_months,
        })

    total_allocated = sum(p["monthly_allocation"] for p in plans)

    return {
        "feasible": True,
        "monthly_surplus": round(surplus, 2),
        "total_allocated": round(total_allocated, 2),
        "unallocated": round(surplus - total_allocated, 2),
        "plans": plans,
    }
