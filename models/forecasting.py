"""
BloxLogicAI — tea export volume forecasting (Prophet).

Univariate monthly model: it learns trend, yearly seasonality and the 2022
economic-crisis shock directly from ~14 years of real export history
(data/processed/forecast_dataset.csv, columns ds, y in MT).

Public API (mirrored by tests/test_forecasting.py):
    load_forecast_data()         -> DataFrame[ds, y]
    train_model(df, **params)    -> fitted Prophet
    predict(model, periods)      -> forecast DataFrame
    evaluate(df, test_periods)   -> {mae, rmse, mape, ...}
    save_model(model, path) / load_model(path)
"""

from __future__ import annotations

import os
import json
import numpy as np
import pandas as pd
import joblib
from prophet import Prophet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "processed", "forecast_dataset.csv")
SAVED = os.path.join(ROOT, "models", "saved")
MODEL_PATH = os.path.join(SAVED, "forecast_prophet.joblib")
METRICS_PATH = os.path.join(SAVED, "forecast_metrics.json")

# Sensible defaults for a monthly volume series ~14 years long.
DEFAULT_PARAMS = dict(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
    seasonality_mode="multiplicative",
    changepoint_prior_scale=0.5,   # allow the 2022 crisis trend break
    interval_width=0.90,
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_forecast_data(path: str = DATA) -> pd.DataFrame:
    """Load the univariate forecast dataset (ds, y) for Prophet."""
    df = pd.read_csv(path, parse_dates=["ds"])
    df = df[["ds", "y"]].dropna().sort_values("ds").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Train / predict
# ---------------------------------------------------------------------------
def train_model(df: pd.DataFrame, **params) -> Prophet:
    """Fit a Prophet model on a (ds, y) frame."""
    cfg = {**DEFAULT_PARAMS, **params}
    model = Prophet(**cfg)
    model.fit(df[["ds", "y"]])
    return model


def predict(model: Prophet, periods: int = 12, freq: str = "MS") -> pd.DataFrame:
    """Forecast `periods` months ahead; returns ds + yhat (+ bounds)."""
    future = model.make_future_dataframe(periods=periods, freq=freq)
    fc = model.predict(future)
    return fc[["ds", "yhat", "yhat_lower", "yhat_upper"]]


# ---------------------------------------------------------------------------
# Evaluate (hold-out backtest)
# ---------------------------------------------------------------------------
def evaluate(df: pd.DataFrame, test_periods: int = 12, **params) -> dict:
    """Hold out the last `test_periods` months, fit on the rest, score them."""
    if len(df) <= test_periods + 12:
        raise ValueError("Not enough history for the requested hold-out.")

    train, test = df.iloc[:-test_periods], df.iloc[-test_periods:]
    model = train_model(train, **params)
    fc = predict(model, periods=test_periods).set_index("ds")
    pred = fc.loc[test["ds"], "yhat"].to_numpy()
    actual = test["y"].to_numpy()

    err = actual - pred
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mape = float(np.mean(np.abs(err / actual)) * 100)
    return {
        "test_periods": int(test_periods),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "train_start": str(train["ds"].min().date()),
        "test_start": str(test["ds"].min().date()),
        "test_end": str(test["ds"].max().date()),
    }


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_model(model: Prophet, path: str = MODEL_PATH) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: str = MODEL_PATH) -> Prophet:
    return joblib.load(path)


# ---------------------------------------------------------------------------
# Pipeline: evaluate -> train on all data -> save
# ---------------------------------------------------------------------------
def main() -> None:
    df = load_forecast_data()
    print(f"Loaded {len(df)} months: {df.ds.min():%Y-%m} -> {df.ds.max():%Y-%m}")

    metrics = evaluate(df, test_periods=12)
    print("Backtest (last 12 months):")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    model = train_model(df)
    save_model(model)
    os.makedirs(SAVED, exist_ok=True)
    with open(METRICS_PATH, "w") as fh:
        json.dump(metrics, fh, indent=2)

    fc = predict(model, periods=12)
    print("\nNext 12-month forecast (MT):")
    print(fc.tail(12).assign(
        yhat=lambda d: d.yhat.round(0),
        yhat_lower=lambda d: d.yhat_lower.round(0),
        yhat_upper=lambda d: d.yhat_upper.round(0),
    ).to_string(index=False))
    print(f"\nSaved model -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
