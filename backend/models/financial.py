from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class IncomeSource(BaseModel):
    name: str
    amount: float = Field(gt=0, description="Monthly income amount")
    frequency: str = Field(default="monthly", pattern="^(monthly|biweekly|weekly|annual)$")
    is_taxable: bool = True
    is_recurring: bool = True


class ExpenseCategory(str, Enum):
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    CHILDCARE = "childcare"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    PERSONAL = "personal"
    SAVINGS = "savings"
    OTHER = "other"


class Expense(BaseModel):
    name: str
    amount: float = Field(gt=0)
    category: ExpenseCategory
    is_fixed: bool = True


class Debt(BaseModel):
    name: str
    balance: float = Field(ge=0)
    interest_rate: float = Field(ge=0, le=100, description="Annual interest rate as percentage")
    minimum_payment: float = Field(ge=0)
    debt_type: str = Field(default="other", pattern="^(mortgage|auto|student|credit_card|personal|medical|other)$")


class SavingsGoal(BaseModel):
    name: str
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0, default=0)
    monthly_contribution: float = Field(ge=0, default=0)
    priority: int = Field(ge=1, le=5, default=3)


class HouseholdProfile(BaseModel):
    income: list[IncomeSource]
    expenses: list[Expense]
    debts: list[Debt] = []
    savings_goals: list[SavingsGoal] = []
    emergency_fund_balance: float = Field(ge=0, default=0)
    tax_rate: float = Field(ge=0, le=100, default=25.0, description="Effective tax rate %")


class ScenarioType(str, Enum):
    INCOME_INCREASE = "income_increase"
    INCOME_DECREASE = "income_decrease"
    EXPENSE_INCREASE = "expense_increase"
    EXPENSE_DECREASE = "expense_decrease"
    NEW_DEBT = "new_debt"
    EXTRA_DEBT_PAYMENT = "extra_debt_payment"
    JOB_LOSS = "job_loss"
    EMERGENCY = "emergency"
    INVESTMENT_RETURN = "investment_return"


class Scenario(BaseModel):
    type: ScenarioType
    description: str = ""
    amount: float = 0
    target_name: Optional[str] = None
    duration_months: Optional[int] = None


class DebtStrategy(str, Enum):
    AVALANCHE = "avalanche"
    SNOWBALL = "snowball"


class DebtListRequest(BaseModel):
    debts: list[Debt]


class ScenarioCompareRequest(BaseModel):
    income: list[IncomeSource]
    expenses: list[Expense]
    debts: list[Debt] = []
    savings_goals: list[SavingsGoal] = []
    emergency_fund_balance: float = Field(ge=0, default=0)
    tax_rate: float = Field(ge=0, le=100, default=25.0)
    scenarios: list[Scenario]

    def to_profile(self) -> "HouseholdProfile":
        return HouseholdProfile(
            income=self.income,
            expenses=self.expenses,
            debts=self.debts,
            savings_goals=self.savings_goals,
            emergency_fund_balance=self.emergency_fund_balance,
            tax_rate=self.tax_rate,
        )
