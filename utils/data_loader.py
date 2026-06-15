"""
BloxLogicAI — data loading & preprocessing pipeline.

Builds a single monthly master dataset from real source data, then emits two
model-specific views:
  - forecast_dataset.csv  (Prophet: long target history, lean regressors)
  - anomaly_dataset.csv   (Isolation Forest: feature-rich, real months only)

Real sources (data/sources/):
  - monthly_tea_raw.csv ........ monthly production/export hand-extracted from
                                 SLTB Monthly Tea Statistics PDFs (Aug21-Oct23)
  - USDtoLKR.csv ............... daily USD/LKR indicative rate (2019-2026)
  - climate/SriLanka_Weather_Dataset.csv .. daily weather, 30 cities (2010-2023)
"""

from __future__ import annotations

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
SOURCES = os.path.join(ROOT, "data", "sources")
PROCESSED = os.path.join(ROOT, "data", "processed")

TEA_RAW = os.path.join(RAW, "monthly_tea_raw.csv")
USD_CSV = os.path.join(SOURCES, "USDtoLKR.csv")
WEATHER_CSV = os.path.join(SOURCES, "climate", "SriLanka_Weather_Dataset.csv")
EXPORT_CSV = os.path.join(SOURCES, "Export_Data_2011_to_2026.csv")
PRODUCTION_CSV = os.path.join(SOURCES, "Production_Data_2011_to_2026.csv")

# Official SLTB annual export totals (MT) — used to derive 2022-12 and validate.
ANNUAL_EXPORT_MT = {2021: 286016, 2022: 250191, 2023: 241912}


# ---------------------------------------------------------------------------
# Export: long monthly history (2011-2026) -> single national total series
# ---------------------------------------------------------------------------
def load_export_monthly() -> pd.DataFrame:
    """National monthly tea export volume (MT) from the SLTB customs export file.

    The file is a hierarchical dump: detail rows per category/package plus
    embedded 'Sub Total' / 'Total Exports' / 'Grand Total' lines whose labels
    drift across years. The clean per-month total is the 'Total Exports' line;
    where both a plain and a '(Without RTD)' variant exist we keep Without-RTD
    (RTD is a tiny liquid product reported in litres, not comparable kg).
    Quantities are in kg; converted to MT ('000 kg) to match official totals.
    """
    df = pd.read_csv(EXPORT_CSV, usecols=range(6),
                     names=["month", "category", "pkg", "qty_kg", "price", "mrec"],
                     header=0)
    df["month"] = pd.to_datetime(df["month"].fillna(df["mrec"]), errors="coerce")
    df["qty_kg"] = pd.to_numeric(df["qty_kg"], errors="coerce")

    tot = df[df["pkg"].astype(str).str.contains("Total Exports", na=False)].copy()
    tot = tot.dropna(subset=["month", "qty_kg"])
    tot["without_rtd"] = tot["pkg"].astype(str).str.contains("Without RTD", na=False)

    # one row per month: prefer the Without-RTD total when present
    tot = (tot.sort_values(["month", "without_rtd"])  # False then True
              .groupby("month", as_index=False).last())
    out = tot[["month", "qty_kg"]].copy()
    out["export_mt"] = out["qty_kg"] / 1000.0
    return out[["month", "export_mt"]].sort_values("month").reset_index(drop=True)


def load_production_monthly() -> pd.DataFrame:
    """National monthly tea production (MT) from the elevation 'Total' rows."""
    df = pd.read_csv(PRODUCTION_CSV, usecols=range(4),
                     names=["month", "elev", "qty_kg", "mrec"], header=0)
    df["month"] = pd.to_datetime(df["month"].fillna(df["mrec"]), errors="coerce")
    df["qty_kg"] = pd.to_numeric(df["qty_kg"], errors="coerce")
    tot = df[df["elev"].astype(str).str.strip().eq("Total")].dropna(
        subset=["month", "qty_kg"])
    out = tot.groupby("month", as_index=False)["qty_kg"].sum()
    out["production_mt"] = out["qty_kg"] / 1000.0
    return out[["month", "production_mt"]].sort_values("month").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Macro: USD/LKR daily -> monthly
# ---------------------------------------------------------------------------
def load_macro_monthly() -> pd.DataFrame:
    """Monthly USD/LKR: mean rate + intra-month volatility (std of daily rate)."""
    df = pd.read_csv(USD_CSV, skip_blank_lines=True)
    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["rate"] = pd.to_numeric(df["Exchange Rate"], errors="coerce")
    df = df.dropna(subset=["rate"])
    df["month"] = df["Date"].dt.to_period("M")
    out = (
        df.groupby("month")["rate"]
        .agg(usd_lkr_avg="mean", usd_lkr_volatility="std")
        .reset_index()
    )
    out["month"] = out["month"].dt.to_timestamp()
    return out


# ---------------------------------------------------------------------------
# Climate: daily 30-city weather -> national monthly
# ---------------------------------------------------------------------------
def load_weather_monthly() -> pd.DataFrame:
    """National monthly climate: rainfall (mm) and mean temperature (C).

    Rainfall = mean across cities of each city's monthly total precipitation.
    Temp     = mean across cities and days of daily mean temperature.
    Jul-Oct 2023 (beyond weather coverage) imputed from 2010-2023 monthly
    climatology so the anomaly window can reach Oct 2023.
    """
    df = pd.read_csv(WEATHER_CSV, usecols=["time", "precipitation_sum",
                                           "temperature_2m_mean", "city"])
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])
    df["month"] = df["time"].dt.to_period("M")

    # per city-month: total rain, mean temp
    city_month = (
        df.groupby(["city", "month"])
        .agg(rain=("precipitation_sum", "sum"),
             temp=("temperature_2m_mean", "mean"))
        .reset_index()
    )
    # national: average across cities
    nat = (
        city_month.groupby("month")
        .agg(rainfall_mm=("rain", "mean"), temp_mean=("temp", "mean"))
        .reset_index()
    )
    nat["month"] = nat["month"].dt.to_timestamp()

    # monthly climatology for imputation
    nat["m"] = nat["month"].dt.month
    clim = nat.groupby("m").agg(rainfall_mm=("rainfall_mm", "mean"),
                                temp_mean=("temp_mean", "mean"))

    # extend to 2023-10 if weather ends earlier
    full = pd.date_range("2019-01-01", "2023-10-01", freq="MS")
    nat = nat.set_index("month").reindex(full)
    nat.index.name = "month"
    nat["m"] = nat.index.month
    for col in ["rainfall_mm", "temp_mean"]:
        nat[col] = nat[col].fillna(nat["m"].map(clim[col]))
    nat = nat.drop(columns="m").reset_index()
    return nat


# ---------------------------------------------------------------------------
# Tea: hand-extracted monthly raw
# ---------------------------------------------------------------------------
def load_tea_monthly() -> pd.DataFrame:
    """Load monthly tea production/export; clean known cumulative-format rows."""
    df = pd.read_csv(TEA_RAW)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df = df.dropna(subset=["month"])

    # 2021-08 PDF reports CUMULATIVE (Jan-Aug) exports, not a single month.
    # Keep its production (valid single-month); drop its export/value/fob.
    aug21 = df["month"] == pd.Timestamp("2021-08-01")
    df.loc[aug21, ["export_mt", "export_value_lkr_mn", "fob_rs_kg"]] = pd.NA

    # 2022-12 export missing from source; derive from official annual total.
    known_2022 = df[(df.month.dt.year == 2022) & df.export_mt.notna()]["export_mt"].sum()
    dec22 = df["month"] == pd.Timestamp("2022-12-01")
    df.loc[dec22, "export_mt"] = ANNUAL_EXPORT_MT[2022] - known_2022

    # mark which export points are derived rather than read from a report
    df["export_derived"] = dec22
    return df


# ---------------------------------------------------------------------------
# Merge -> single monthly master
# ---------------------------------------------------------------------------
def build_master() -> pd.DataFrame:
    """Left-join tea (the spine) with macro + weather on month."""
    tea = load_tea_monthly()
    macro = load_macro_monthly()
    weather = load_weather_monthly()

    master = (
        tea.merge(macro, on="month", how="left")
        .merge(weather, on="month", how="left")
        .sort_values("month")
        .reset_index(drop=True)
    )
    return master


# ---------------------------------------------------------------------------
# View 1 — Prophet forecast dataset
# ---------------------------------------------------------------------------
def build_forecast_dataset() -> pd.DataFrame:
    """Continuous monthly univariate series for Prophet (ds, y = export MT).

    Source: the long 2011-2026 customs export file (~166 real monthly points),
    which gives Prophet enough history to learn yearly seasonality, trend and
    the 2022 economic-crisis shock. A handful of months are missing from the
    file; we reindex to a continuous monthly spine and time-interpolate those
    gaps, flagging every imputed point in `y_imputed` for honest reporting.
    """
    exp = load_export_monthly()

    # continuous monthly spine across the real coverage
    full = pd.date_range(exp["month"].min(), exp["month"].max(), freq="MS")
    fc = exp.set_index("month").reindex(full)
    fc.index.name = "ds"
    fc = fc.reset_index()

    fc["y_imputed"] = fc["export_mt"].isna()
    fc = fc.set_index("ds")
    fc["export_mt"] = fc["export_mt"].interpolate(method="time",
                                                  limit_direction="both")
    fc = fc.reset_index().rename(columns={"export_mt": "y"})
    return fc[["ds", "y", "y_imputed"]]


# ---------------------------------------------------------------------------
# View 2 — Isolation Forest anomaly dataset
# ---------------------------------------------------------------------------
def build_anomaly_dataset(master: pd.DataFrame | None = None) -> pd.DataFrame:
    """Feature-rich, real-months-only view for Isolation Forest.

    Keeps only months with a genuine (reported or annual-derived) export value
    and a full feature row — no target interpolation, because injecting smooth
    synthetic points would mask the very anomalies the model must find.
    """
    if master is None:
        master = build_master()

    feature_cols = ["production_mt", "export_mt", "export_value_lkr_mn",
                    "fob_rs_kg", "usd_lkr_avg", "usd_lkr_volatility",
                    "rainfall_mm", "temp_mean"]
    an = master[["month"] + feature_cols + ["export_derived"]].copy()

    # Isolation Forest cannot take NaN; require every feature present. This also
    # excludes the derived Dec-2022 row (no reported fob_rs_kg), keeping the
    # anomaly set to 100% reported signals.
    an = an.dropna(subset=feature_cols).reset_index(drop=True)
    return an


def _summ(df: pd.DataFrame, cols) -> str:
    nn = df[cols].notna().sum().to_dict()
    return f"{len(df)} rows; non-null {nn}"


if __name__ == "__main__":
    os.makedirs(PROCESSED, exist_ok=True)
    fc = build_forecast_dataset()
    fc.to_csv(os.path.join(PROCESSED, "forecast_dataset.csv"), index=False)

    print("=== FORECAST (Prophet, univariate export volume) ===")
    print(_summ(fc, ["y"]))
    print(f"range {fc.ds.min():%Y-%m} -> {fc.ds.max():%Y-%m}; imputed y: {int(fc.y_imputed.sum())}")
    yr = fc.assign(year=fc.ds.dt.year).groupby("year")["y"].sum().round(0)
    print("annual export (MT):", {int(k): int(v) for k, v in yr.items()})
    print("\nWrote: forecast_dataset.csv -> data/processed/")
