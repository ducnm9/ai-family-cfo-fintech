from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class FamilyMember(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="member", pattern="^(owner|spouse|child|parent|other|member)$")


class FamilyMemberResponse(BaseModel):
    id: int
    name: str
    role: str


class CloseMonthRequest(BaseModel):
    month: str = Field(pattern=r'^\d{4}-\d{2}$', description="YYYY-MM format")
    notes: Optional[str] = ""


class SnapshotSummary(BaseModel):
    id: int
    month: str
    notes: str
    closed_at: str
    total_income: float
    total_expenses: float
    total_debt_balance: float
    monthly_buffer: float


class SnapshotDetail(BaseModel):
    id: int
    month: str
    notes: str
    closed_at: str
    data: dict
    summary: dict
