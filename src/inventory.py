from __future__ import annotations

import numpy as np
import pandas as pd
from statistics import NormalDist


def optimize_replenishment(forecasts: pd.DataFrame, service_level: float = 0.95, budget: float | None = None) -> pd.DataFrame:
    z = NormalDist().inv_cdf(min(max(service_level, 0.50), 0.999))
    rows = []
    for (store_id, product_id), group in forecasts.groupby(["store_id", "product_id"]):
        group = group.sort_values("date")
        first = group.iloc[0]
        lead = max(1, int(first.lead_time_days))
        demand = group.forecast.head(lead).sum()
        sigma = float(first.residual_std) * np.sqrt(lead)
        safety = z * sigma
        reorder_point = demand + safety
        on_hand = float(first.on_hand)
        raw = max(0, reorder_point - on_hand)
        pack = max(1, int(first.pack_size))
        moq = max(1, int(first.moq))
        qty = int(np.ceil(raw / pack) * pack) if raw > 0 else 0
        if qty > 0:
            qty = max(moq, qty)
        qty = min(qty, int(first.supplier_capacity))
        if qty > 0:
            qty = int(np.floor(qty / pack) * pack)
        cost = qty * float(first.unit_cost)
        priority = (demand + safety) / max(on_hand, 1)
        rows.append({"store_id": store_id, "product_id": product_id, "category": first.category, "on_hand": on_hand, "lead_time_days": lead, "lead_time_demand": demand, "demand_std_lead_time": sigma, "safety_stock": safety, "reorder_point": reorder_point, "recommended_order_qty": qty, "unit_cost": first.unit_cost, "estimated_order_cost": cost, "stockout_risk": "HIGH" if on_hand < demand else ("MEDIUM" if on_hand < reorder_point else "LOW"), "priority_score": priority, "supplier_capacity": first.supplier_capacity, "moq": moq, "pack_size": pack})
    result = pd.DataFrame(rows).sort_values("priority_score", ascending=False).reset_index(drop=True)
    result["budget_limited_qty"] = result.recommended_order_qty
    if budget is not None:
        remaining = budget
        for idx, row in result.iterrows():
            affordable = int(remaining // max(float(row.unit_cost), 0.01))
            pack = int(row.pack_size)
            affordable = affordable // pack * pack
            result.loc[idx, "budget_limited_qty"] = min(int(row.recommended_order_qty), affordable)
            remaining -= result.loc[idx, "budget_limited_qty"] * float(row.unit_cost)
    return result
