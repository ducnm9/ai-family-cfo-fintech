import json
from fastapi import APIRouter, HTTPException, Depends, status

from models.user import (
    UserRegister, UserLogin, UserResponse, UserUpdate,
    PasswordChange, TokenResponse, FamilyMember, FamilyMemberResponse,
    CloseMonthRequest, SnapshotSummary, SnapshotDetail,
)
from auth.security import (
    hash_password, verify_password, create_access_token, get_current_user_id,
)
from db.database import get_wrapped_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
profile_router = APIRouter(prefix="/api/v1/user", tags=["user"])


def _user_response(u: dict) -> UserResponse:
    return UserResponse(
        id=u["id"],
        email=u["email"],
        full_name=u["full_name"],
        is_active=bool(u["is_active"]),
        created_at=str(u["created_at"]),
    )


# ---------- Auth ----------

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: UserRegister):
    db = get_wrapped_db()
    existing = db.execute("SELECT id FROM users WHERE email = %s", (req.email,)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(req.password)
    db.execute(
        "INSERT INTO users (email, full_name, hashed_password) VALUES (%s, %s, %s) RETURNING id",
        (req.email, req.full_name, hashed),
    )
    user_id = db.lastrowid
    db.execute(
        "INSERT INTO profiles (user_id, data) VALUES (%s, %s)",
        (user_id, json.dumps({})),
    )
    db.commit()

    user = db.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    db.close()

    token = create_access_token(user_id, req.email)
    return TokenResponse(access_token=token, user=_user_response(user))


@router.post("/login", response_model=TokenResponse)
def login(req: UserLogin):
    db = get_wrapped_db()
    user = db.execute("SELECT * FROM users WHERE email = %s", (req.email,)).fetchone()
    db.close()

    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(access_token=token, user=_user_response(user))


# ---------- User profile ----------

@profile_router.get("/me", response_model=UserResponse)
def get_me(user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    user = db.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    db.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_response(user)


@profile_router.patch("/me", response_model=UserResponse)
def update_me(req: UserUpdate, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    updates = []
    params = []
    if req.full_name is not None:
        updates.append("full_name = %s")
        params.append(req.full_name)
    if req.email is not None:
        existing = db.execute(
            "SELECT id FROM users WHERE email = %s AND id != %s", (req.email, user_id)
        ).fetchone()
        if existing:
            db.close()
            raise HTTPException(status_code=409, detail="Email already in use")
        updates.append("email = %s")
        params.append(req.email)

    if not updates:
        db.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    params.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
    db.commit()

    user = db.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    db.close()
    return _user_response(user)


@profile_router.post("/me/change-password")
def change_password(req: PasswordChange, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    user = db.execute("SELECT hashed_password FROM users WHERE id = %s", (user_id,)).fetchone()
    if not verify_password(req.current_password, user["hashed_password"]):
        db.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    hashed = hash_password(req.new_password)
    db.execute("UPDATE users SET hashed_password = %s, updated_at = NOW() WHERE id = %s", (hashed, user_id))
    db.commit()
    db.close()
    return {"message": "Password updated successfully"}


# ---------- Financial profile (save/load) ----------

@profile_router.get("/profile")
def get_financial_profile(user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    row = db.execute("SELECT data FROM profiles WHERE user_id = %s", (user_id,)).fetchone()
    db.close()
    if not row:
        return {}
    data = row["data"]
    return data if isinstance(data, dict) else json.loads(data)


@profile_router.put("/profile")
def save_financial_profile(data: dict, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    json_data = json.dumps(data)
    db.execute(
        "INSERT INTO profiles (user_id, data) VALUES (%s, %s) "
        "ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()",
        (user_id, json_data),
    )
    db.commit()
    db.close()
    return {"message": "Profile saved"}


# ---------- Family members ----------

@profile_router.get("/family", response_model=list[FamilyMemberResponse])
def list_family(user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    rows = db.execute(
        "SELECT id, name, role FROM family_members WHERE user_id = %s", (user_id,)
    ).fetchall()
    db.close()
    return [FamilyMemberResponse(id=r["id"], name=r["name"], role=r["role"]) for r in rows]


@profile_router.post("/family", response_model=FamilyMemberResponse, status_code=201)
def add_family_member(member: FamilyMember, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    db.execute(
        "INSERT INTO family_members (user_id, name, role) VALUES (%s, %s, %s) RETURNING id",
        (user_id, member.name, member.role),
    )
    member_id = db.lastrowid
    db.commit()
    db.close()
    return FamilyMemberResponse(id=member_id, name=member.name, role=member.role)


@profile_router.delete("/family/{member_id}")
def remove_family_member(member_id: int, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    row = db.execute(
        "SELECT id FROM family_members WHERE id = %s AND user_id = %s", (member_id, user_id)
    ).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Member not found")
    db.execute("DELETE FROM family_members WHERE id = %s", (member_id,))
    db.commit()
    db.close()
    return {"message": "Member removed"}


# ---------- Monthly snapshots ----------

@profile_router.post("/snapshots", status_code=201)
def close_month(req: CloseMonthRequest, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()

    existing = db.execute(
        "SELECT id FROM monthly_snapshots WHERE user_id = %s AND month = %s",
        (user_id, req.month),
    ).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=409, detail="This month is already closed")

    profile_row = db.execute("SELECT data FROM profiles WHERE user_id = %s", (user_id,)).fetchone()
    if not profile_row:
        db.close()
        raise HTTPException(status_code=400, detail="No financial profile to snapshot")

    data = profile_row["data"]
    if isinstance(data, str):
        data = json.loads(data)

    # Compute summary
    income = sum(i.get("amount", 0) for i in data.get("income", []))
    expenses = sum(e.get("amount", 0) for e in data.get("expenses", []))
    debt_payments = sum(d.get("minimum_payment", 0) for d in data.get("debts", []))
    debt_balance = sum(d.get("balance", 0) for d in data.get("debts", []))
    tax_rate = data.get("tax_rate", 25)
    net_income = income * (1 - tax_rate / 100)
    buffer = net_income - expenses - debt_payments

    summary = {
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "total_debt_balance": round(debt_balance, 2),
        "total_debt_payments": round(debt_payments, 2),
        "monthly_buffer": round(buffer, 2),
        "net_income": round(net_income, 2),
    }

    db.execute(
        "INSERT INTO monthly_snapshots (user_id, month, data, summary, notes) VALUES (%s, %s, %s, %s, %s)",
        (user_id, req.month, json.dumps(data), json.dumps(summary), req.notes or ""),
    )

    # --- Rollover ---
    next_income = [i for i in data.get("income", []) if i.get("is_recurring", True)]
    next_expenses = [e for e in data.get("expenses", []) if e.get("is_fixed", False)]
    next_debts = []
    for d in data.get("debts", []):
        new_balance = d.get("balance", 0) - d.get("minimum_payment", 0)
        if new_balance > 0.01:
            next_debts.append({**d, "balance": round(new_balance, 2)})

    next_emergency = data.get("emergency_fund_balance", 0)
    if buffer > 0:
        next_emergency = round(next_emergency + buffer, 2)

    next_profile = {
        "income": next_income,
        "expenses": next_expenses,
        "debts": next_debts,
        "savings_goals": data.get("savings_goals", []),
        "emergency_fund_balance": next_emergency,
        "tax_rate": data.get("tax_rate", 25),
    }

    next_json = json.dumps(next_profile)
    db.execute(
        "INSERT INTO profiles (user_id, data) VALUES (%s, %s) "
        "ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()",
        (user_id, next_json),
    )

    db.commit()
    db.close()

    rollover = {
        "income_kept": len(next_income),
        "income_cleared": len(data.get("income", [])) - len(next_income),
        "expenses_kept": len(next_expenses),
        "expenses_cleared": len(data.get("expenses", [])) - len(next_expenses),
        "debts_remaining": len(next_debts),
        "debts_paid_off": len(data.get("debts", [])) - len(next_debts),
        "emergency_fund_new": next_emergency,
    }

    return {"message": f"Month {req.month} closed", "summary": summary, "rollover": rollover}


@profile_router.get("/snapshots", response_model=list[SnapshotSummary])
def list_snapshots(user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    rows = db.execute(
        "SELECT id, month, notes, closed_at, summary FROM monthly_snapshots WHERE user_id = %s ORDER BY month DESC",
        (user_id,),
    ).fetchall()
    db.close()
    result = []
    for r in rows:
        s = r["summary"] if isinstance(r["summary"], dict) else json.loads(r["summary"])
        result.append(SnapshotSummary(
            id=r["id"], month=r["month"], notes=r["notes"] or "", closed_at=str(r["closed_at"]),
            total_income=s.get("total_income", 0),
            total_expenses=s.get("total_expenses", 0),
            total_debt_balance=s.get("total_debt_balance", 0),
            monthly_buffer=s.get("monthly_buffer", 0),
        ))
    return result


@profile_router.get("/snapshots/{month}", response_model=SnapshotDetail)
def get_snapshot(month: str, user_id: int = Depends(get_current_user_id)):
    db = get_wrapped_db()
    row = db.execute(
        "SELECT * FROM monthly_snapshots WHERE user_id = %s AND month = %s",
        (user_id, month),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    data = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    summary = row["summary"] if isinstance(row["summary"], dict) else json.loads(row["summary"])
    return SnapshotDetail(
        id=row["id"], month=row["month"], notes=row["notes"] or "",
        closed_at=str(row["closed_at"]),
        data=data,
        summary=summary,
    )
