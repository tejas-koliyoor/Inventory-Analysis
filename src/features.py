from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(data: pd.DataFrame) -> pd.DataFrame:
    df = data.sort_values(["store_id", "product_id", "date"]).copy()
    g = df.groupby(["store_id", "product_id"], sort=False)["demand"]
    for lag in (1, 7, 14, 28, 56):
        df[f"lag_{lag}"] = g.shift(lag)
    shifted = g.shift(1)
    for window in (7, 28, 56):
        df[f"rolling_mean_{window}"] = shifted.groupby([df.store_id, df.product_id]).transform(lambda s: s.rolling(window, min_periods=window).mean())
        df[f"rolling_std_{window}"] = shifted.groupby([df.store_id, df.product_id]).transform(lambda s: s.rolling(window, min_periods=window).std())
    df["day_of_week"] = df.date.dt.dayofweek
    df["day_of_year"] = df.date.dt.dayofyear
    df["month"] = df.date.dt.month
    df["quarter"] = df.date.dt.quarter
    df["week_of_month"] = ((df.date.dt.day - 1) // 7 + 1).astype(int)
    df["is_month_start"] = df.date.dt.is_month_start.astype(int)
    df["is_month_end"] = df.date.dt.is_month_end.astype(int)
    df["season_sin"] = np.sin(2 * np.pi * df.date.dt.dayofyear / 365.25)
    df["season_cos"] = np.cos(2 * np.pi * df.date.dt.dayofyear / 365.25)
    df["week_of_year"] = df.date.dt.isocalendar().week.astype(int)
    df["is_weekend"] = (df.day_of_week >= 5).astype(int)
    df["time_index"] = (df.date - df.date.min()).dt.days
    return df.dropna(subset=["lag_56", "rolling_std_56"]).reset_index(drop=True)


FEATURES = ["store_id", "product_id", "promo", "price", "lead_time_days", "day_of_week", "day_of_year", "month", "quarter", "week_of_year", "week_of_month", "is_weekend", "is_month_start", "is_month_end", "season_sin", "season_cos", "time_index", "lag_1", "lag_7", "lag_14", "lag_28", "lag_56", "rolling_mean_7", "rolling_mean_28", "rolling_mean_56", "rolling_std_7", "rolling_std_28", "rolling_std_56"]
