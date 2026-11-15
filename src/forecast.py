from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

from .features import FEATURES


def _wape(y, pred):
    return float(np.abs(y - pred).sum() / max(np.abs(y).sum(), 1))


def _models(seed: int):
    models = {
        "random_forest": make_pipeline(SimpleImputer(), RandomForestRegressor(n_estimators=100, min_samples_leaf=3, max_features=0.8, n_jobs=-1, random_state=seed)),
    }
    try:
        from xgboost import XGBRegressor
        models["xgboost"] = make_pipeline(SimpleImputer(), XGBRegressor(n_estimators=180, max_depth=7, learning_rate=0.06, subsample=0.85, colsample_bytree=0.85, objective="reg:squarederror", n_jobs=-1, random_state=seed, verbosity=0))
    except ImportError:
        pass
    return models


def evaluate_models(df: pd.DataFrame, folds: int = 3, seed: int = 42, sample_size: int = 120_000):
    dates = np.sort(df.date.unique())
    validation_days = max(14, min(28, len(dates) // (folds + 2)))
    start = len(dates) - folds * validation_days
    model_map = _models(seed)
    rows, residuals = [], {}
    for fold in range(folds):
        cut = start + fold * validation_days
        train_dates = dates[:cut]
        valid_dates = dates[cut:cut + validation_days]
        train = df[df.date.isin(train_dates)]
        valid = df[df.date.isin(valid_dates)]
        if len(train) > sample_size:
            train = train.sample(sample_size, random_state=seed + fold)
        y = valid.demand.to_numpy()
        preds = {"seasonal_naive": valid.lag_7.to_numpy(), "moving_average": valid.rolling_mean_7.to_numpy()}
        for name, model in model_map.items():
            model.fit(train[FEATURES], train.demand)
            preds[name] = np.maximum(0, model.predict(valid[FEATURES]))
        for name, pred in preds.items():
            err = y - pred
            rows.append({"model": name, "fold": fold + 1, "train_end": pd.Timestamp(train_dates[-1]), "valid_start": pd.Timestamp(valid_dates[0]), "valid_end": pd.Timestamp(valid_dates[-1]), "mae": mean_absolute_error(y, pred), "rmse": mean_squared_error(y, pred) ** 0.5, "wape": _wape(y, pred)})
            residuals.setdefault(name, []).extend(err.tolist())
    metrics = pd.DataFrame(rows)
    summary = metrics.groupby("model").wape.mean().sort_values()
    return metrics, summary.index[0], {k: float(np.std(v)) for k, v in residuals.items()}, model_map


def fit_and_forecast(features: pd.DataFrame, model_name: str, seed: int, residual_std: dict, model_map: dict, horizon: int = 14):
    last_date = features.date.max()
    output = []
    groups = features.groupby(["store_id", "product_id"], sort=False)
    for (store_id, product_id), history in groups:
        history = history.sort_values("date")
        recent = history.tail(28)
        base = history.demand.tail(56).to_numpy()
        sigma = residual_std.get(model_name, float(np.std(base) + 1))
        for step in range(1, horizon + 1):
            date = last_date + pd.Timedelta(days=step)
            row = history.iloc[-1].copy()
            row["date"] = date
            row["promo"] = 0
            row["day_of_week"] = date.dayofweek
            row["day_of_year"] = date.dayofyear
            row["month"] = date.month
            row["quarter"] = date.quarter
            row["week_of_month"] = (date.day - 1) // 7 + 1
            row["is_month_start"] = int(date.is_month_start)
            row["is_month_end"] = int(date.is_month_end)
            row["season_sin"] = np.sin(2 * np.pi * date.dayofyear / 365.25)
            row["season_cos"] = np.cos(2 * np.pi * date.dayofyear / 365.25)
            row["week_of_year"] = int(date.isocalendar().week)
            row["is_weekend"] = int(date.dayofweek >= 5)
            row["time_index"] = int(row.time_index) + step
            row["lag_1"] = base[-1]
            row["lag_7"] = base[-7] if len(base) >= 7 else np.mean(base)
            row["lag_14"] = base[-14] if len(base) >= 14 else np.mean(base)
            row["lag_28"] = base[-28] if len(base) >= 28 else np.mean(base)
            row["lag_56"] = base[-56] if len(base) >= 56 else np.mean(base)
            row["rolling_mean_7"] = np.mean(base[-7:])
            row["rolling_mean_28"] = np.mean(base[-28:])
            row["rolling_std_7"] = np.std(base[-7:])
            row["rolling_std_28"] = np.std(base[-28:])
            row["rolling_mean_56"] = np.mean(base[-56:])
            row["rolling_std_56"] = np.std(base[-56:])
            if model_name == "seasonal_naive":
                pred = max(0, row.lag_7)
            elif model_name == "moving_average":
                pred = max(0, row.rolling_mean_7)
            else:
                pred = max(0, float(model_map[model_name].predict(pd.DataFrame([row[FEATURES]], columns=FEATURES))[0]))
            output.append({"date": date, "store_id": store_id, "product_id": product_id, "category": row.category, "forecast": pred, "lower_95": max(0, pred - 1.96 * sigma), "upper_95": pred + 1.96 * sigma, "model": model_name, "lead_time_days": row.lead_time_days, "unit_cost": row.unit_cost, "on_hand": row.on_hand, "supplier_capacity": row.supplier_capacity, "moq": row.moq, "pack_size": row.pack_size, "holding_cost_rate": row.holding_cost_rate, "stockout_penalty": row.stockout_penalty, "residual_std": sigma})
            base = np.append(base, pred)
    return pd.DataFrame(output)
