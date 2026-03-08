# Financial Optimization Engine

Responsible for deterministic financial simulation and optimization.

Inputs: - income_sources - fixed_expenses - variable_expenses - debts -
savings - goals

Core metric: monthly_buffer = income - expenses - minimum_debt_payments

Stress index: stress = mandatory_expenses / income

Simulation runs monthly and outputs: - debt_free_date -
savings_projection - risk_periods
