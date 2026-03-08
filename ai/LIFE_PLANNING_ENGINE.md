
# Life Planning Engine

Purpose:
Simulate major life events and their financial impact.

Directory:
backend/app/life_planning/

File:
life_event_engine.py

Supported events:

buy_house
have_child
career_change
job_loss
start_business
retirement

Example simulation:

Input:
{
  "event": "buy_house",
  "price": 1200000000,
  "down_payment": 300000000,
  "mortgage_rate": 0.09
}

Output:

{
  "monthly_payment": 10800000,
  "impact_on_cashflow": -10800000,
  "goal_delay": "2 years"
}

Engine logic:

1. Modify financial state
2. Inject new expense or debt
3. Rerun simulation engine
4. Compare baseline vs scenario
