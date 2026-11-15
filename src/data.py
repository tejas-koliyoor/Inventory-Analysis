from __future__ import annotations

import numpy as np
import pandas as pd


def generate_data(days: int = 730, stores: int = 20, products: int = 30, seed: int = 42) -> pd.DataFrame:
    """Generate deterministic synthetic daily sales and inventory input."""
    if days < 120 or stores < 1 or products < 1:
        raise ValueError("days must be >= 120 and stores/products must be positive")
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=1), periods=days, freq="D")
    store_ids = np.arange(1, stores + 1)
    product_ids = np.arange(1, products + 1)
    grid = pd.MultiIndex.from_product([dates, store_ids, product_ids], names=["date", "store_id", "product_id"]).to_frame(index=False)
    n = len(grid)
    product_base = rng.uniform(5, 28, products)
    store_factor = rng.lognormal(0, 0.22, stores)
    category = (grid.product_id.to_numpy() - 1) % 6
    dow = grid.date.dt.dayofweek.to_numpy()
    doy = grid.date.dt.dayofyear.to_numpy()
    promo = rng.binomial(1, 0.09, n)
    price = rng.uniform(8, 80, products)[grid.product_id.to_numpy() - 1]
    price *= np.where(promo == 1, 0.85, 1.0)
    weekly = np.choose(dow, [0.91, 0.94, 0.99, 1.02, 1.12, 1.24, 1.18])
    yearly = 1 + 0.18 * np.sin(2 * np.pi * doy / 365.25) + 0.08 * np.cos(4 * np.pi * doy / 365.25)
    trend = 1 + np.arange(n) / max(n, 1) * 0.08
    store = grid.store_id.to_numpy() - 1
    product = grid.product_id.to_numpy() - 1
    mean = product_base[product] * store_factor[store] * weekly * yearly * trend * (1 + 0.35 * promo)
    demand = rng.poisson(np.maximum(mean, 0.2)).astype(int)
    lead = rng.integers(2, 15, n)
    unit_cost = price * rng.uniform(0.42, 0.68, n)
    initial_stock = np.maximum(0, np.rint(mean * rng.uniform(4, 12, n))).astype(int)
    grid["category"] = np.array([f"Category-{c+1}" for c in category])
    grid["promo"] = promo
    grid["price"] = np.round(price, 2)
    grid["demand"] = demand
    grid["lead_time_days"] = lead
    grid["unit_cost"] = np.round(unit_cost, 2)
    grid["on_hand"] = initial_stock
    grid["supplier_capacity"] = np.maximum(20, np.rint(mean * 35)).astype(int)
    grid["moq"] = rng.choice([1, 6, 12], n, p=[0.65, 0.25, 0.10])
    grid["pack_size"] = rng.choice([1, 1, 6, 12], n)
    grid["holding_cost_rate"] = 0.22
    grid["stockout_penalty"] = np.round(price * 0.75, 2)
    return grid
