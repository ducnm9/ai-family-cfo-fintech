"""Net Worth Engine — Track and forecast total wealth over time."""

from models.v3 import NetWorthInput


def compute_net_worth(input: NetWorthInput) -> dict:
    """
    net_worth = assets - liabilities
    Project forward with expected returns.
    """
    total_assets = sum(a.value for a in input.assets)
    net_worth = total_assets - input.total_debt

    # Breakdown by type
    by_type = {}
    for a in input.assets:
        t = a.asset_type.value
        by_type[t] = by_type.get(t, 0) + a.value

    # Project forward 10 years
    timeline = {}
    projected_assets = {a.name: a.value for a in input.assets}
    projected_debt = input.total_debt

    for year in range(0, 11):
        year_label = str(2026 + year)

        # Grow assets by their return rate
        year_total = 0
        for a in input.assets:
            val = projected_assets[a.name]
            if year > 0:
                val *= (1 + a.annual_return_pct / 100)
                val += input.monthly_savings * 12 / len(input.assets) if input.assets else 0
                projected_assets[a.name] = val
            year_total += val

        # Reduce debt (simplified: assume 5% reduction per year from payments)
        if year > 0:
            projected_debt = max(0, projected_debt * 0.85)

        timeline[year_label] = round(year_total - projected_debt, 2)

    # Asset allocation percentages
    allocation = {}
    if total_assets > 0:
        for t, v in by_type.items():
            allocation[t] = round(v / total_assets * 100, 1)

    return {
        "net_worth": round(net_worth, 2),
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(input.total_debt, 2),
        "assets_by_type": {k: round(v, 2) for k, v in by_type.items()},
        "allocation_pct": allocation,
        "timeline": timeline,
        "assets_detail": [
            {"name": a.name, "type": a.asset_type.value, "value": round(a.value, 2), "return_pct": a.annual_return_pct}
            for a in input.assets
        ],
    }
