
# FINANCIAL_ALGORITHMS.md

## Purpose
Define the core financial algorithms used in AI Family CFO V2.

These algorithms must remain deterministic unless explicitly marked probabilistic.

---

# 1. Cashflow Simulation

monthly_buffer = income - expenses - minimum_debt_payments

Pseudo:

for month in timeline:
    income = sum(incomes)
    expenses = sum(expenses)
    debt_payment = sum(minimum_payments)
    buffer = income - expenses - debt_payment

Output:
- monthly buffer
- savings update
- debt reduction

---

# 2. Debt Avalanche Algorithm

Goal:
Pay highest interest debt first.

Pseudo:

sort debts by interest_rate descending

while debts remain:
    pay minimums
    allocate extra payment to highest interest debt

---

# 3. Debt Snowball Algorithm

Goal:
Pay smallest balance first.

Pseudo:

sort debts by principal ascending

while debts remain:
    pay minimums
    allocate extra payment to smallest balance

---

# 4. Financial Stress Index

stress_index = mandatory_expenses / income

Mandatory expenses include:
- housing
- food
- utilities
- minimum debt payments

Interpretation:

< 0.5   Healthy
0.5-0.7 Moderate
> 0.7   High Stress

---

# 5. Financial Resilience

resilience_months = savings / monthly_expense

Example:
savings = 60M
expense = 20M

resilience = 3 months

---

# 6. Monte Carlo Financial Simulation

Purpose:
Estimate uncertainty in financial future.

Pseudo:

for simulation in range(1000):

    income = random.normal(mean_income, income_std)

    expenses = random.normal(mean_expense, expense_std)

    run deterministic simulation

Collect statistics:
- probability debt free
- probability negative cashflow

---

# 7. Income Forecast

Use moving average.

forecast = average(last_n_months)

Example:
last 6 months income average

---

# 8. Expense Forecast

Moving average or exponential smoothing.

forecast_expense = average(last_6_months)

---

# 9. Financial Health Score

score = weighted_sum(

    debt_ratio,
    savings_rate,
    resilience,
    goal_progress

)

Example weights:

debt_ratio: 30%
savings_rate: 25%
resilience: 25%
goal_progress: 20%
