from fastapi import APIRouter

from models.financial import (
    HouseholdProfile, Scenario, DebtStrategy, Debt,
    DebtListRequest, ScenarioCompareRequest,
)
from simulation.engine import simulate_cashflow, project_forward
from simulation.debt_engine import optimize_debt_payoff, compare_strategies
from simulation.scenario_engine import run_scenario_comparison, stress_test
from advisor.rules_engine import generate_recommendations

router = APIRouter(prefix="/api/v1", tags=["finance"])


@router.get("/overview")
def overview():
    return {
        "message": "AI Family CFO API",
        "endpoints": [
            "POST /api/v1/simulate",
            "POST /api/v1/simulate/project",
            "POST /api/v1/debt/optimize",
            "POST /api/v1/debt/compare",
            "POST /api/v1/scenario/compare",
            "POST /api/v1/scenario/stress-test",
            "POST /api/v1/advisor/recommendations",
        ],
    }


@router.post("/simulate")
def simulate(profile: HouseholdProfile):
    return simulate_cashflow(profile)


@router.post("/simulate/project")
def project(profile: HouseholdProfile, months: int = 12):
    return {
        "current": simulate_cashflow(profile),
        "projections": project_forward(profile, months),
    }


@router.post("/debt/optimize")
def debt_optimize(
    req: DebtListRequest,
    extra_payment: float = 0,
    strategy: DebtStrategy = DebtStrategy.AVALANCHE,
):
    return optimize_debt_payoff(req.debts, extra_payment, strategy)


@router.post("/debt/compare")
def debt_compare(req: DebtListRequest, extra_payment: float = 0):
    return compare_strategies(req.debts, extra_payment)


@router.post("/scenario/compare")
def scenario_compare(req: ScenarioCompareRequest):
    profile = req.to_profile()
    return run_scenario_comparison(profile, req.scenarios)


@router.post("/scenario/stress-test")
def scenario_stress_test(profile: HouseholdProfile):
    return stress_test(profile)


@router.post("/advisor/recommendations")
def advisor_recommendations(profile: HouseholdProfile):
    return {
        "cashflow": simulate_cashflow(profile),
        "recommendations": generate_recommendations(profile),
    }
