"""V3 Pydantic models for life planning, goals, assets, decisions, and memory."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# --- Life Events ---

class LifeEventType(str, Enum):
    BUY_HOUSE = "buy_house"
    HAVE_CHILD = "have_child"
    CAREER_CHANGE = "career_change"
    JOB_LOSS = "job_loss"
    START_BUSINESS = "start_business"
    RETIREMENT = "retirement"


class LifeEventInput(BaseModel):
    event: LifeEventType
    price: float = 0
    down_payment: float = 0
    mortgage_rate: float = 0.08
    mortgage_years: int = 20
    new_income: float = 0
    new_monthly_expense: float = 0
    income_loss_months: int = 0
    startup_cost: float = 0
    retirement_age: int = 60
    retirement_monthly_need: float = 0


# --- Goals ---

class GoalType(str, Enum):
    EMERGENCY_FUND = "emergency_fund"
    BUY_HOUSE = "buy_house"
    EDUCATION_FUND = "education_fund"
    RETIREMENT = "retirement"
    CUSTOM = "custom"


class FinancialGoal(BaseModel):
    name: str
    goal_type: GoalType = GoalType.CUSTOM
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0, default=0)
    priority: int = Field(ge=1, le=5, default=3)
    deadline_months: Optional[int] = None


class GoalListRequest(BaseModel):
    goals: list[FinancialGoal]
    monthly_surplus: float = Field(ge=0)


# --- Assets ---

class AssetType(str, Enum):
    CASH = "cash"
    STOCKS = "stocks"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    BONDS = "bonds"
    OTHER = "other"


class Asset(BaseModel):
    name: str
    asset_type: AssetType
    value: float = Field(ge=0)
    annual_return_pct: float = Field(default=0, description="Expected annual return %")


class NetWorthInput(BaseModel):
    assets: list[Asset]
    total_debt: float = Field(ge=0, default=0)
    monthly_savings: float = Field(ge=0, default=0)


# --- Decision ---

class DecisionOption(BaseModel):
    name: str
    description: str = ""
    new_debt: float = 0
    new_monthly_expense: float = 0
    new_monthly_income: float = 0
    upfront_cost: float = 0
    asset_value: float = 0


class DecisionRequest(BaseModel):
    question: str
    options: list[DecisionOption] = Field(min_length=2)


# --- Memory ---

class LifeEventRequest(BaseModel):
    profile: "HouseholdProfile"
    event: LifeEventInput


class DecisionFullRequest(BaseModel):
    profile: "HouseholdProfile"
    request: DecisionRequest


class MemoryEntry(BaseModel):
    category: str
    content: str
    metadata: dict = {}


from models.financial import HouseholdProfile  # noqa: E402
LifeEventRequest.model_rebuild()
DecisionFullRequest.model_rebuild()
