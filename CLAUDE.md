# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

**BloxLogicAI** — *AI and Blockchain-Enabled Supply Chain Forecasting & Analysis System for Sri Lanka's Tea Industry.*

BSc (Hons) Software Engineering final-year dissertation (CL/BSCSD/33/160, Cardiff Metropolitan University via ICBT). Submission: 2026-06-29. Single lightweight Python web app — no database, no cloud. Storage is flat files (CSV/JSON). Runs locally with `streamlit run app/main.py`.

---

## 1. The three modules

| # | Module | Tech | Status |
|---|--------|------|--------|
| 1 | **Forecasting** — monthly tea export volume | Prophet (univariate + multivariate) | ✅ Done, tested |
| 2 | **Anomaly detection** — flag supply-chain disruptions | Isolation Forest (scikit-learn) | ✅ Wired end-to-end (`models/anomaly.py` → `data/anomaly_alerts.json`); no dedicated unit tests yet |
| 3 | **Blockchain traceability** — immutable tea-batch ledger | SHA-256 hash chain | ✅ Per-batch ledger + QR generation + user/admin UI done, tested (18 tests) |

Authentication and role-based routing (user / admin portals) are fully implemented.

---

## 2. Environment

- **Always use the project venv:** `.venv/Scripts/python.exe` — not the global `Python310`.
- **cmdstanpy pin is critical:** Prophet 1.1.5 ships a stripped cmdstan. `cmdstanpy==1.2.4` is pinned in `requirements.txt` — do **not** bump it. Newer versions reject the stripped installation with `CmdStan installation missing makefile`.
- **Default admin credentials:** `admin` / `admin123` (or override via `BLOXLOGIC_ADMIN_PASSWORD` env var). Created automatically on first run if no admin exists in `data/users.csv`.

---

## 3. Common commands

```bash
# Run the app (from project root)
.venv/Scripts/python.exe -m streamlit run app/main.py

# Run all tests
.venv/Scripts/python.exe -m pytest tests/ -v

# Run a single test file
.venv/Scripts/python.exe -m pytest tests/test_forecasting.py -v

# Run a single test
.venv/Scripts/python.exe -m pytest tests/test_auth.py::test_hash_round_trip -v

# Rebuild processed datasets from sources (requires data/sources/ files)
.venv/Scripts/python.exe utils/data_loader.py

# Train / backtest the univariate model (default)
.venv/Scripts/python.exe models/forecasting.py

# Train / backtest the multivariate model
.venv/Scripts/python.exe models/forecasting.py --model multivariate

# Seed the blockchain ledger with 3 demo tea batches
.venv/Scripts/python.exe blockchain/ledger.py
```

---

## 4. Repository layout

```
BloxLogicAI/
├── app/
│   ├── main.py              # Entry point + router (public pages / role-based dispatch)
│   ├── auth.py              # PBKDF2 password hashing, CSV user store, session helpers
│   ├── config.py            # Centralised path constants — import from here, not ROOT-derived
│   ├── style.py             # inject_theme(), metric_card(), badge(), rec_box(), panel()
│   └── views/
│       ├── landing.py       # Public landing page
│       ├── login.py         # Login form
│       ├── register.py      # Registration form
│       ├── user_dashboard.py
│       ├── forecast.py      # Forecasting dashboard (univariate + multivariate toggle)
│       ├── anomaly.py       # Anomaly alert cards (reads anomaly_alerts.json)
│       ├── blockchain_trace.py  # Batch search + timeline (reads blockchain_ledger.json)
│       ├── admin_dashboard.py
│       ├── admin_dataset.py
│       ├── admin_forecast.py  # Train / retrain Prophet, shows MAPE/MAE/RMSE
│       ├── admin_anomaly.py   # Runs Isolation Forest on demand, shows alerts
│       ├── admin_ledger.py    # Admin blockchain management
│       ├── admin_users.py
│       └── analytics.py
├── models/
│   ├── forecasting.py       # Prophet pipeline: load/train/predict/evaluate/save/load
│   ├── anomaly.py           # Isolation Forest: run_anomaly_detection() → ANOMALY_PATH
│   └── saved/                # forecast_prophet.joblib, forecast_metrics.json (committed)
│                              # forecast_prophet_mv.joblib, forecast_metrics_mv.json
├── blockchain/
│   ├── ledger.py              # Per-batch SHA-256 hash chains: add_block, verify_chain, get_batch, next_stage
│   └── qr_generator.py        # QR generation + scanning (FR10): format_batch_trace, generate_qr_png_bytes, decode_qr_image, extract_batch_id
├── utils/
│   └── data_loader.py        # Data pipeline → processed/ views
├── data/
│   ├── sources/               # Raw third-party CSVs — GITIGNORED (large)
│   ├── raw/                   # Extracted raw (committed)
│   ├── processed/             # forecast_univariant.csv, forecast_multivariant.csv,
│   │                          # anomaly_detection.csv, production_monthly.csv,
│   │                          # fx_monthly.csv, weather_tea_monthly.csv
│   ├── blockchain_ledger.json # Demo chain with 3 batches / 14 blocks (committed)
│   ├── anomaly_alerts.json    # Anomaly alerts output (committed if generated)
│   └── users.csv              # GITIGNORED — runtime credential store (password hashes)
└── tests/
    ├── test_forecasting.py   # 5 tests: train, predict shape, evaluate, save/load, real data
    ├── test_auth.py          # 7 tests: hash, verify, add_user, authenticate, seed admin
    ├── test_ledger.py        # 16 tests: hash determinism, per-batch verify_chain, stage-order enforcement, tamper detection
    └── test_qr_generator.py  # 2 tests: PNG output, payload normalization
```

Note: `models/anomaly.py` has no dedicated test file yet (only forecasting, auth, and ledger are covered under `tests/`).

---

## 5. Data pipeline (`utils/data_loader.py`)

Models never read `data/sources/` directly — the loader builds model-specific views.

### Sources (`data/sources/`, gitignored)
- `Export_Data_2011_to_2026.csv` — SLTB customs dump. Use `Total Exports (Without RTD)` row per month. `qty` in kg → ÷1000 = MT. Yields ~175 monthly points (2011-10 → 2026-04).
- `Production_Data_2011_to_2026.csv` — monthly by elevation; use `Total` rows.
- `usd_lkr_historical.csv` + `sri_lanka_weather_data/*.csv` — anomaly / multivariate features.
- `crude_oil_history.csv`, `brent_crude_history.csv`, `fuel_prices_lk.csv` — anomaly-detection features (crude oil, fuel/kerosene prices).
- `Sales_Data_2011_to_2026.csv` — too sparse; dropped.

### Output datasets (`data/processed/`, committed)
| File | Path constant (`app/config.py`) | Columns |
|------|----------------------------------|---------|
| `forecast_univariant.csv` | `FORECAST_CSV` | `ds, y, y_imputed` — univariate spine |
| `forecast_multivariant.csv` | `MV_FORECAST_CSV` | `ds, y, production_mt, usd_lkr_avg, rainfall_mm, temp_mean` + `*_imputed` flags |
| `anomaly_detection.csv` | `ANOMALY_CSV` | `month, production_mt, export_mt, usd_lkr_avg, usd_lkr_volatility, rainfall_mm, temp_mean, crude_oil_price, brent_crude_price, fuel_lp92, fuel_lad, kerosene_price` (no interpolation — see below) |
| `production_monthly.csv` | — | Monthly production by elevation zone |
| `fx_monthly.csv` | — | USD/LKR monthly avg + volatility |
| `weather_tea_monthly.csv` | — | Production-weighted tea-region climate |

Missing months on the forecast spine are time-interpolated and flagged `y_imputed=True`. The anomaly dataset intentionally skips interpolation — smooth synthetic points would mask anomalies. Filenames use "univariant"/"multivariant" (not the standard spelling) — this is the actual on-disk/code naming, not a typo to silently "fix".

---

## 6. Forecasting module (`models/forecasting.py`)

Exposes two Prophet models behind a shared API:

**Shared primitives** (imported by views and tests):
- `load_forecast_data()` / `load_multivariate_data()` → cleaned DataFrame
- `train_model(df, regressors=())` → fitted Prophet (no regressors = univariate)
- `predict(model, periods=12)` → `ds/yhat/yhat_lower/yhat_upper` (univariate)
- `predict_multivariate(model, history, regressors, periods)` → same schema
- `evaluate(df, test_periods=12, regressors=())` → `{mae, rmse, mape, ...}`
- `save_model` / `load_model` → joblib persistence

**Model runners** (orchestrate backtest → full-train → persist):
- `run_univariate_model(df)` → persists to `MODEL_PATH` / `METRICS_PATH`
- `run_multivariate_model(df)` → persists to `MV_MODEL_PATH` / `MV_METRICS_PATH`

**Multivariate pattern**: future driver values are cascade-forecast — each regressor (`production_mt`, `usd_lkr_avg`, `rainfall_mm`, `temp_mean`) is projected ahead by its own lightweight Prophet before the main model predicts. `make_future_regressors()` accepts `overrides` dict for what-if scenarios (fixed value or callable transform).

**DEFAULT_PARAMS**: `yearly_seasonality=True`, `seasonality_mode="multiplicative"`, `changepoint_prior_scale=0.5` (captures the 2022 crisis trend break), `interval_width=0.90`.

**Backtest results** (12-month hold-out):
- Univariate: MAPE 9.06%, MAE ~1768 MT, RMSE ~1977 MT
- Multivariate: see `models/saved/forecast_metrics_mv.json`

Note: `MODEL_PATH`/`METRICS_PATH` are defined in both `app/config.py` and `models/forecasting.py` (kept in sync). `MV_MODEL_PATH`/`MV_METRICS_PATH`/`MV_REGRESSORS` exist only in `models/forecasting.py` — `app/config.py` has no multivariate-model path constants.

---

## 7. Blockchain module (`blockchain/ledger.py`, `blockchain/qr_generator.py`)

**Per-batch SHA-256 hash chains** — each tea batch owns its own independent chain; a block's `previous_hash` links only to the prior block of the *same* batch, seeded at `GENESIS_HASH = "0" * 16`. This is deliberate: `verify_chain()` on one batch's blocks is unaffected by tampering in a different batch. Each block hashes `batch_id|seq|stage|location|details|timestamp|previous_hash`, where `seq` is the batch's own 1-based block index (not a global counter).

**Stage lifecycle** — `STAGE_ORDER = ["Harvested", "Processed", "Blended", "Packaged", "Exported"]`. `add_block()` enforces strict per-batch ordering: no skipping, no duplicates, no adding after a batch reaches `Exported`. Violations raise `InvalidStageError` (a `ValueError` subclass).

Key functions: `add_block(batch_id, stage, location, details, timestamp=None)`, `verify_chain(blocks)`, `get_batch(batch_id)`, `next_stage(batch_id, blocks=None)`, `load_ledger()`, `save_ledger()`.

`blockchain/ledger.py` intentionally re-derives `ROOT`/`LEDGER_PATH` locally (same pattern as `models/forecasting.py`) rather than importing `app.config`, so it can be run as a standalone script:
```bash
.venv/Scripts/python.exe blockchain/ledger.py             # wipe and re-seed demo data (3 batches: TEA001–TEA003, 14 blocks total)
.venv/Scripts/python.exe blockchain/ledger.py --tamper     # non-destructive tamper-detection demo (dissertation viva) — mutates an in-memory copy only, never touches the saved file
```

**QR code generation (FR10)** — `blockchain/qr_generator.py` exposes `batch_qr_payload(batch_id)` (normalizes to uppercase/trimmed), `format_batch_trace(batch_id, blocks)` (builds the human-readable multi-line payload — every recorded stage's location/details, ending with the batch ID), and `generate_qr_png_bytes(data, box_size=12, border=2)` (renders in-memory PNG bytes via `qrcode`, no disk writes). QR codes encode the **batch's full recorded journey as plain text**, not just the batch ID and not a deep-link URL — the app runs fully offline/local (NFR1), so any phone's camera/QR app can read the complete stage-by-stage history with zero dependency on this app or a network. Timestamps are deliberately omitted from the QR payload to keep it small and reliably scannable (they're already shown in the app's timeline view). The payload is also ASCII-sanitized (`unicodedata` NFKD transliteration) before encoding — some QR encoder/decoder implementations mis-round-trip non-ASCII bytes like `°` by misreading them as Kanji-mode segments, corrupting the scanned text; staying ASCII avoids this for every scanner, not just ours. The batch ID is included at the end so a viewer can still search it in the app to run the cryptographic VALID/TAMPERED integrity check. Wired into both `app/views/blockchain_trace.py` (per-batch QR + download) and `app/views/admin_ledger.py` (admin QR generator for any batch).

**In-app QR scanner** — `app/views/blockchain_trace.py` has a camera icon beside the search bar. Clicking it opens a panel with `st.camera_input()`; the captured photo is decoded via `qr_generator.decode_qr_image()` (`pyzbar`, lazily imported so the dependency only loads on the scan path) and the batch ID is pulled back out of the decoded trace text via `qr_generator.extract_batch_id()` (regex on the `TEA BATCH TRACE - <ID>` header line `format_batch_trace()` writes — the two functions are a matched encode/decode pair). A successful scan stores the ID in `st.session_state["scanned_batch_id"]` and reruns; the results section renders identically to a manual text search (a typed Batch ID always takes priority and clears any prior scan). This lets a phone scan a printed batch QR *from the website's camera* and land on the same result page as searching by ID — no manual typing needed. `pyzbar==0.1.9` is pinned in `requirements.txt` (its Windows wheel bundles the required `libzbar` DLLs, no separate system install needed).

**Tamper-detection demo** ships two ways: the `--tamper` CLI flag above, and a "Run Tamper Demo" button in `app/views/admin_ledger.py` — both operate on an in-memory `copy.deepcopy()` and never mutate `data/blockchain_ledger.json`.

---

## 8. Streamlit app architecture (`app/`)

**Router pattern** (`app/main.py`):
1. Public (unauthenticated) — dispatches to `landing`, `login`, or `register` via `st.session_state.page`.
2. Authenticated — role-based sidebar radio dispatches to view modules via lazy imports (keeps Prophet off the public path).

**All view modules expose exactly one `render()` function.** The router calls `render()` directly.

**Session state keys** managed by `app/auth.py`:
- `authenticated` (bool), `user` (dict with username/email/role), `page` (str)

**Path constants** — always import from `app/config.py`, not re-derived per module:
```python
from app.config import FORECAST_CSV, LEDGER_PATH, ANOMALY_PATH, MODEL_PATH, USERS_CSV
```

**Style system** (`app/style.py`):
- `inject_theme()` — call once in `main.py`; injects badge/timeline/status-row CSS
- `metric_card(label, value, delta, positive, note)` — inline-CSS KPI card
- `badge(severity)` → HTML `<span>` (HIGH/MEDIUM/LOW)
- `rec_box(label, value)` — amber recommendation box
- `panel(title)` — section heading with green underline

**Performance**: forecast views use `@st.cache_data` (data, metrics) and `@st.cache_resource` (model). Call `.clear()` on all three after retraining.

**Anomaly view note**: `app/views/anomaly.py` reads `data/anomaly_alerts.json`. The Isolation Forest model is wired end-to-end — `app/views/admin_anomaly.py`'s "Run Anomaly Detection" button calls `models/anomaly.run_anomaly_detection()`, which fits `IsolationForest(contamination=0.10)` on `ANOMALY_CSV` and overwrites `ANOMALY_PATH`. Severity/type per alert is assigned by simple quantile heuristics on export volume, fuel price, and crude oil price (not learned).

---

## 9. Authentication (`app/auth.py`)

Flat-file CSV store (`data/users.csv` — gitignored). Password format: `pbkdf2_sha256$260000$<salt_hex>$<hash_hex>` (standard library only, no bcrypt dependency). Thread-safe writes via `threading.Lock()`.

Key functions: `hash_password`, `verify_password`, `add_user`, `remove_user`, `update_password`, `authenticate`, `ensure_seed_admin`.

Constant-time login path: missing usernames call `verify_password` against a dummy hash to prevent timing-based username enumeration.

---

## 10. Conventions & workflow

- **Venv:** always `.venv/Scripts/python.exe`
- **Code style:** `from __future__ import annotations`, type hints, concise docstrings, section banner comments (`# ---`)
- **Path constants:** centralise in `app/config.py`, not re-derived per file
- **Git commits** must end with: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **Commit / push only when the user asks.**
- **.gitignore policy:** only `data/sources/` (large), `models/saved/*.pkl`, `data/users.csv`. Everything else — `data/raw/`, `data/processed/`, `*.joblib`, `*_metrics.json`, `blockchain_ledger.json` — is committed for examiner reproducibility.
- Shell commands must be prefixed with `rtk` (token-optimizing passthrough; safe on all commands).
- Keep changes scoped to the current module; don't pre-build later modules.

---

*Full functional/non-functional requirements and acceptance criteria: `docs/REQUIREMENTS.md`.*
