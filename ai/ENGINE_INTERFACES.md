
# ENGINE_INTERFACES.md

## Purpose
Define interfaces between engines so modules remain decoupled.

---

# 1. Simulation Engine Interface

Input:

{
  income_sources,
  expenses,
  debts,
  savings
}

Output:

{
  cashflow_timeline,
  debt_timeline,
  savings_timeline,
  stress_index
}

---

# 2. Risk Engine Interface

Input:

financial_state

Output:

{
  risk_score,
  flags
}

Flags examples:

HIGH_DEBT_RATIO
LOW_EMERGENCY_FUND
HIGH_STRESS

---

# 3. Forecast Engine Interface

Input:

income_history
expense_history

Output:

{
  income_forecast_12m,
  expense_forecast_12m
}

---

# 4. Monte Carlo Engine Interface

Input:

financial_state

parameters:

{
  income_variance,
  expense_variance,
  simulations
}

Output:

{
  probability_debt_free,
  probability_negative_cashflow
}

---

# 5. Optimization Engine Interface

Input:

financial_state

Output:

{
  recommended_debt_payment,
  recommended_savings_rate,
  recommended_expense_reduction
}

---

# 6. Advisor Engine Interface

Input:

simulation_result
risk_result
optimization_result

Output:

{
  recommendations,
  explanations,
  projected_improvements
}
