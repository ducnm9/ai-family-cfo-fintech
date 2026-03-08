"""Behavior Engine — Detect spending patterns and behavioral flags."""

import json


def analyze_behavior(snapshots: list[dict]) -> dict:
    """
    Analyze spending behavior across monthly snapshots.
    Detects: overspending, lifestyle inflation, category growth.
    """
    if len(snapshots) < 2:
        return {
            "has_data": False,
            "message": "Need at least 2 months of history for behavior analysis.",
            "patterns": [],
        }

    # Parse snapshots into structured data
    months = []
    for snap in sorted(snapshots, key=lambda s: s.get("month", "")):
        data = snap.get("data", {})
        if isinstance(data, str):
            data = json.loads(data)
        summary = snap.get("summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)

        # Category breakdown from snapshot data
        categories = {}
        for exp in data.get("expenses", []):
            cat = exp.get("category", "other")
            categories[cat] = categories.get(cat, 0) + exp.get("amount", 0)

        months.append({
            "month": snap["month"],
            "total_income": summary.get("total_income", 0),
            "total_expenses": summary.get("total_expenses", 0),
            "buffer": summary.get("monthly_buffer", 0),
            "categories": categories,
        })

    patterns = []
    latest = months[-1]
    previous = months[-2]

    # Overall spending growth
    if previous["total_expenses"] > 0:
        expense_growth = (latest["total_expenses"] - previous["total_expenses"]) / previous["total_expenses"] * 100
        if expense_growth > 10:
            patterns.append({
                "type": "OVERSPENDING",
                "severity": "high" if expense_growth > 20 else "medium",
                "description": f"Expenses grew {expense_growth:.1f}% from last month",
                "value": round(expense_growth, 1),
                "threshold": 10,
            })

    # Lifestyle inflation: income and expenses both growing
    if len(months) >= 3:
        first = months[0]
        if first["total_income"] > 0 and first["total_expenses"] > 0:
            income_growth = (latest["total_income"] - first["total_income"]) / first["total_income"] * 100
            expense_growth_total = (latest["total_expenses"] - first["total_expenses"]) / first["total_expenses"] * 100

            if income_growth > 5 and expense_growth_total > income_growth * 0.8:
                patterns.append({
                    "type": "LIFESTYLE_INFLATION",
                    "severity": "medium",
                    "description": f"Expenses growing at {expense_growth_total:.1f}% while income grew {income_growth:.1f}%",
                    "value": round(expense_growth_total, 1),
                    "threshold": round(income_growth, 1),
                })

    # Category growth detection
    all_cats = set()
    for m in months:
        all_cats.update(m["categories"].keys())

    category_changes = []
    for cat in all_cats:
        prev_val = previous["categories"].get(cat, 0)
        curr_val = latest["categories"].get(cat, 0)
        if prev_val > 0:
            pct_change = (curr_val - prev_val) / prev_val * 100
            if pct_change > 20:
                category_changes.append({
                    "category": cat,
                    "previous": round(prev_val, 2),
                    "current": round(curr_val, 2),
                    "change_pct": round(pct_change, 1),
                })

    if category_changes:
        for cc in sorted(category_changes, key=lambda x: x["change_pct"], reverse=True)[:3]:
            patterns.append({
                "type": "CATEGORY_GROWTH",
                "severity": "medium" if cc["change_pct"] > 30 else "low",
                "description": f"{cc['category']} spending grew {cc['change_pct']:.1f}%",
                "category": cc["category"],
                "value": cc["change_pct"],
                "threshold": 20,
            })

    # Consistent negative buffer
    negative_months = sum(1 for m in months if m["buffer"] < 0)
    if negative_months >= 2:
        patterns.append({
            "type": "PERSISTENT_DEFICIT",
            "severity": "critical",
            "description": f"Negative cashflow for {negative_months} of {len(months)} months",
            "value": negative_months,
            "threshold": 2,
        })

    return {
        "has_data": True,
        "months_analyzed": len(months),
        "patterns": patterns,
        "summary": {
            "latest_expenses": round(latest["total_expenses"], 2),
            "latest_buffer": round(latest["buffer"], 2),
            "avg_expenses": round(sum(m["total_expenses"] for m in months) / len(months), 2),
        },
    }
