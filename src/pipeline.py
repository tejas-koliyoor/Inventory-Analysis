from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from .data import generate_data
from .features import add_features
from .forecast import evaluate_models, fit_and_forecast
from .inventory import optimize_replenishment

def run(days=730, stores=20, products=30, seed=42, horizon=14, out_dir="data/processed", budget=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"Generating {days * stores * products:,} synthetic store-product-day rows...")
    raw = generate_data(days, stores, products, seed)
    features = add_features(raw)
    print("Evaluating forecasting models with expanding-window validation...")
    metrics, selected, residual_std, model_map = evaluate_models(features, seed=seed)
    print(f"Selected model by mean WAPE: {selected}")
    forecasts = fit_and_forecast(features, selected, seed, residual_std, model_map, horizon)
    recommendations = optimize_replenishment(forecasts, budget=budget)
    raw["promo_demand"] = raw.demand * raw.promo
    daily = raw.groupby("date", as_index=False).agg(sales_units=("demand", "sum"), promo_units=("promo_demand", "sum"))
    daily["promo_share"] = daily.promo_units / raw.groupby("date").demand.sum().to_numpy().clip(min=1)
    metrics.to_csv(out / "model_metrics.csv", index=False)
    forecasts.to_csv(out / "forecasts.csv", index=False)
    recommendations.to_csv(out / "recommendations.csv", index=False)
    daily.to_csv(out / "daily_sales.csv", index=False)
    print(f"Wrote outputs to {out.resolve()}")
    return metrics, forecasts, recommendations

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic demand forecasts and replenishment recommendations")
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--stores", type=int, default=20)
    parser.add_argument("--products", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--horizon", type=int, default=14)
    parser.add_argument("--out-dir", default="data/processed")
    parser.add_argument("--budget", type=float, default=None, help="Optional total purchasing budget")
    a = parser.parse_args()
    run(a.days, a.stores, a.products, a.seed, a.horizon, a.out_dir, a.budget)

if __name__ == "__main__":
    main()
