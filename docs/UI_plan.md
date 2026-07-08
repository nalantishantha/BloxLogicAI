# BloxLogicAI — UI Implementation Plan

**Demo deadline:** Friday 2026-06-20  
**Approach:** Hardcoded data for all non-forecasting sections; real Prophet data reused for Forecasting page.

---

## Design System

### Colors

```python
# Use these as CSS variables injected via st.markdown()
PRIMARY       = "#2E7D32"   # dark green — borders, headings, sidebar accent
PRIMARY_LIGHT = "#4CAF50"   # lighter green — hover, active states
PRIMARY_PALE  = "#C8E6C9"   # very light green — card borders, dividers
ACCENT        = "#F9A825"   # amber/gold — warnings, recommended export highlight
BG            = "#F8FBF8"   # app background (override Streamlit default)
CARD_BG       = "#FFFFFF"   # card white
TEXT          = "#1A1A1A"   # primary text
TEXT_MUTED    = "#666666"   # secondary text/labels
DANGER        = "#C62828"   # high severity alerts
DANGER_LIGHT  = "#FFEBEE"   # high alert background
WARNING       = "#E65100"   # medium severity
WARNING_LIGHT = "#FFF3E0"   # medium alert background
SUCCESS       = "#1B5E20"   # chain valid, positive delta
BORDER        = "#C8E6C9"   # subtle card borders
```

### Typography & Icons
- Use Streamlit's default font (Inter/system-ui). No custom fonts.
- **No colorful emoji** (no 🍃🌿📊💹). Use:
  - Unicode symbols: `▲ ▼ → ← · — ✓ ✗ ⚠`
  - Or plain text labels
- Delta arrows in `st.metric()` are automatic and acceptable (they are styled arrows, not emoji).

### Component Rules
- Cards: `st.container(border=True)` with `st.metric()` inside — clean and Streamlit-native.
- Section headers: `st.header()` or `st.subheader()`
- Dividers: `st.divider()` between major sections
- Tables: `st.dataframe()` for data, `st.markdown()` with HTML for styled badge columns
- Severity badges: inline `<span>` with colored background (see pattern below)
- All `st.markdown()` with HTML requires `unsafe_allow_html=True`

---

## File Structure

```
app/
├── main.py              MODIFY — full role-based routing
├── style.py             CREATE — inject_theme() CSS helper
├── auth.py              unchanged
└── views/
    ├── landing.py       unchanged
    ├── login.py         unchanged (no role selector)
    ├── register.py      unchanged
    ├── forecast.py      unchanged — reused as Forecasting page
    │
    ├── user_dashboard.py    CREATE
    ├── anomaly.py           CREATE
    ├── blockchain_trace.py  CREATE
    │
    ├── admin_dashboard.py   CREATE
    ├── admin_dataset.py     CREATE
    ├── admin_model.py       CREATE
    ├── admin_ledger.py      CREATE
    ├── admin_users.py       CREATE
    └── analytics.py         CREATE

blockchain/
└── ledger.py            CREATE — SHA-256 helpers (load/save/add/verify)

data/
├── blockchain_ledger.json   CREATE — pre-populated hardcoded batches
└── anomaly_alerts.json      CREATE — pre-populated anomaly alerts
```

---

## Step 1 — Create `app/style.py`

This module injects the global CSS theme into every page.

```python
from __future__ import annotations
import streamlit as st

_CSS = """
<style>
/* ── App background ── */
.stApp { background-color: #F8FBF8; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #1B5E20;
}
section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #FFFFFF !important;
    font-size: 14px;
}

/* ── st.container(border=True) card style ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #C8E6C9 !important;
    border-left: 4px solid #2E7D32 !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    padding: 8px !important;
}

/* ── st.metric label ── */
[data-testid="stMetricLabel"] { color: #666666 !important; font-size: 13px; }
[data-testid="stMetricValue"] { color: #1A1A1A !important; font-size: 24px; font-weight: 700; }

/* ── Buttons ── */
.stButton > button {
    background-color: #2E7D32;
    color: white;
    border: none;
    border-radius: 6px;
}
.stButton > button:hover {
    background-color: #1B5E20;
    color: white;
}

/* ── Severity badge helpers (use via st.markdown) ── */
.badge-high   { background:#FFEBEE; color:#C62828; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold; }
.badge-medium { background:#FFF3E0; color:#E65100; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold; }
.badge-low    { background:#F1F8E9; color:#33691E; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold; }

/* ── Blockchain status ── */
.chain-valid   { color:#1B5E20; font-weight:700; font-size:16px; }
.chain-invalid { color:#C62828; font-weight:700; font-size:16px; }
</style>
"""

def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
```

---

## Step 2 — Create Data Files

### `data/anomaly_alerts.json`

```json
[
  {
    "date": "2022-04",
    "type": "Economic Crisis / Fuel Shortage",
    "severity": "HIGH",
    "action": "Reduce export targets by 20%; activate currency hedging",
    "description": "Sri Lanka economic crisis caused severe fuel shortages affecting transport and factory operations."
  },
  {
    "date": "2021-07",
    "type": "Fertiliser Ban — Production Drop",
    "severity": "HIGH",
    "action": "Source alternative organic inputs; notify international buyers of lower volumes",
    "description": "Government ban on chemical fertilisers caused a sharp drop in tea yields across all elevations."
  },
  {
    "date": "2020-04",
    "type": "COVID-19 Supply Disruption",
    "severity": "HIGH",
    "action": "Monitor shipping delays; build buffer stock for key buyers",
    "description": "Pandemic lockdowns disrupted port operations and reduced export volumes significantly."
  },
  {
    "date": "2023-10",
    "type": "Export Volume Drop",
    "severity": "MEDIUM",
    "action": "Review production capacity and re-evaluate demand forecasts",
    "description": "Unexplained dip in monthly export volume — 14% below seasonal average."
  },
  {
    "date": "2023-02",
    "type": "FX Rate Spike (USD/LKR > 360)",
    "severity": "MEDIUM",
    "action": "Expedite pending shipments to lock in favourable exchange rates",
    "description": "Rapid LKR depreciation created short-term pricing advantage but increased uncertainty."
  }
]
```

### `data/blockchain_ledger.json`

Each block structure:
```json
{
  "block_num": 1,
  "batch_id": "TEA001",
  "stage": "Harvested",
  "location": "Nuwara Eliya Estate",
  "details": "2,500 kg Orthodox Black Tea harvested",
  "timestamp": "2026-01-05T08:00:00",
  "previous_hash": "0000000000000000",
  "current_hash": "<computed SHA-256>"
}
```

Pre-populate with 3 batches (13 blocks total):
- **TEA001** — 5 blocks: Harvested (Nuwara Eliya) → Processed (Factory A) → Blended (Colombo) → Packaged (Export Hub) → Exported (UK)
- **TEA002** — 3 blocks: Harvested (Kandy Estate) → Processed (Factory B) → Packaged (Export Hub) [awaiting export]
- **TEA003** — 5 blocks: Harvested (Uva Estate) → Processed (Factory C) → Blended (Colombo) → Packaged (Export Hub) → Exported (UAE)

> Generate the actual JSON by running `blockchain/ledger.py` as a script which seeds the ledger. The hashes must be real SHA-256 values so `verify_chain()` passes.

---

## Step 3 — Create `blockchain/ledger.py`

```python
from __future__ import annotations
import hashlib, json, os
from datetime import datetime

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "blockchain_ledger.json")


def _hash_block(batch_id: str, stage: str, details: str,
                timestamp: str, previous_hash: str) -> str:
    content = f"{batch_id}{stage}{details}{timestamp}{previous_hash}"
    return hashlib.sha256(content.encode()).hexdigest()


def load_ledger() -> list[dict]:
    if not os.path.exists(LEDGER_PATH):
        return []
    with open(LEDGER_PATH, "r") as f:
        return json.load(f)


def save_ledger(blocks: list[dict]) -> None:
    with open(LEDGER_PATH, "w") as f:
        json.dump(blocks, f, indent=2)


def add_block(batch_id: str, stage: str, location: str, details: str) -> dict:
    blocks = load_ledger()
    previous_hash = blocks[-1]["current_hash"] if blocks else "0" * 16
    timestamp = datetime.now().isoformat(timespec="seconds")
    current_hash = _hash_block(batch_id, stage, details, timestamp, previous_hash)
    block = {
        "block_num": len(blocks) + 1,
        "batch_id": batch_id.upper().strip(),
        "stage": stage,
        "location": location,
        "details": details,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
        "current_hash": current_hash,
    }
    blocks.append(block)
    save_ledger(blocks)
    return block


def verify_chain(blocks: list[dict]) -> bool:
    """Return True if every block's current_hash matches a fresh computation."""
    for i, blk in enumerate(blocks):
        expected = _hash_block(
            blk["batch_id"], blk["stage"], blk["details"],
            blk["timestamp"], blk["previous_hash"]
        )
        if blk["current_hash"] != expected:
            return False
        if i > 0 and blk["previous_hash"] != blocks[i - 1]["current_hash"]:
            return False
    return True


def get_batch(batch_id: str) -> list[dict]:
    return [b for b in load_ledger() if b["batch_id"] == batch_id.upper().strip()]


# ── Seed script (run once to generate blockchain_ledger.json) ──────────────
if __name__ == "__main__":
    import os, sys
    # clear existing ledger
    if os.path.exists(LEDGER_PATH):
        os.remove(LEDGER_PATH)

    seed_data = [
        ("TEA001","Harvested","Nuwara Eliya Estate","2,500 kg Orthodox Black Tea harvested"),
        ("TEA001","Processed","Tea Factory A, Nuwara Eliya","Withered 18h, CTC rolled, dried at 90°C"),
        ("TEA001","Blended","Colombo Blending Hub","Blended with BOPF grade, moisture 3.2%"),
        ("TEA001","Packaged","Colombo Export Hub","Packed in 50 kg foil bags, lot #NE-2601"),
        ("TEA001","Exported","Port of Colombo → Destination: UK","Container HLCU4421839, shipped 2026-01-12"),

        ("TEA002","Harvested","Kandy Estate","1,800 kg CTC Black Tea harvested"),
        ("TEA002","Processed","Tea Factory B, Kandy","Withered 16h, CTC processed, dried"),
        ("TEA002","Packaged","Colombo Export Hub","Packed in 50 kg foil bags, lot #KD-2601"),

        ("TEA003","Harvested","Uva Estate","2,200 kg BOP Grade harvested"),
        ("TEA003","Processed","Tea Factory C, Badulla","Processed orthodox method"),
        ("TEA003","Blended","Colombo Blending Hub","Blended with OP grade"),
        ("TEA003","Packaged","Colombo Export Hub","Packed in 50 kg foil bags, lot #UV-2601"),
        ("TEA003","Exported","Port of Colombo → Destination: UAE","Container MSCU3312765, shipped 2026-01-22"),
    ]

    for batch_id, stage, location, details in seed_data:
        b = add_block(batch_id, stage, location, details)
        print(f"Block {b['block_num']:>2} | {batch_id} | {stage:<12} | {b['current_hash'][:16]}...")

    blocks = load_ledger()
    print(f"\nChain valid: {verify_chain(blocks)}")
    print(f"Total blocks: {len(blocks)}")
```

Run it once with: `.venv/Scripts/python.exe blockchain/ledger.py`

---

## Step 4 — Update `app/main.py`

Replace the authenticated section only. Keep public page routing unchanged.

```python
from __future__ import annotations
import os, sys

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import auth
from app.views import landing, login, register
from app.style import inject_theme

st.set_page_config(
    page_title="BloxLogicAI — Tea Supply-Chain Intelligence",
    page_icon="🍃", layout="wide"
)

inject_theme()
auth.init_session()

PUBLIC_PAGES = {"landing": landing, "login": login, "register": register}

if not auth.is_authenticated():
    page = st.session_state.page
    if page not in PUBLIC_PAGES:
        page = "landing"
    PUBLIC_PAGES[page].render()
else:
    user = auth.current_user()
    role = user["role"]

    # ── Sidebar ─────────────────────────────────────────────────────────────
    st.sidebar.title("BloxLogicAI")
    st.sidebar.caption("Sri Lanka Tea Supply-Chain Intelligence")
    st.sidebar.markdown(f"**{user['username']}** · _{role}_")
    if st.sidebar.button("Sign out", use_container_width=True):
        auth.logout_user()
        st.rerun()
    st.sidebar.divider()

    # ── Navigation ───────────────────────────────────────────────────────────
    if role == "admin":
        NAV = ["Dashboard", "Dataset Management", "Model Management",
               "Blockchain Ledger", "User Management", "Analytics"]
    else:
        NAV = ["Dashboard", "Forecasting", "Anomaly Detection", "Blockchain Traceability"]

    page = st.sidebar.radio("Menu", NAV, label_visibility="collapsed")

    # ── Route ────────────────────────────────────────────────────────────────
    if role == "admin":
        if page == "Dashboard":
            from app.views import admin_dashboard; admin_dashboard.render()
        elif page == "Dataset Management":
            from app.views import admin_dataset; admin_dataset.render()
        elif page == "Model Management":
            from app.views import admin_model; admin_model.render()
        elif page == "Blockchain Ledger":
            from app.views import admin_ledger; admin_ledger.render()
        elif page == "User Management":
            from app.views import admin_users; admin_users.render()
        elif page == "Analytics":
            from app.views import analytics; analytics.render()
    else:
        if page == "Dashboard":
            from app.views import user_dashboard; user_dashboard.render()
        elif page == "Forecasting":
            from app.views import forecast; forecast.render()
        elif page == "Anomaly Detection":
            from app.views import anomaly; anomaly.render()
        elif page == "Blockchain Traceability":
            from app.views import blockchain_trace; blockchain_trace.render()
```

---

## Step 5 — User-Facing Views

### `app/views/user_dashboard.py`

Layout: 4 KPI cards → divider → 2-column (Export Recommendation | Anomaly Summary)

```
HEADER: "Dashboard"
SUBHEADER: "Supply Chain Overview — Sri Lanka Tea Industry | June 2026"

─── 4 KPI CARDS (st.columns(4)) ───────────────────────────────────────────
[col1] st.container(border=True)
  st.metric("Current Production", "24,221 MT", "+3.2%")

[col2] st.container(border=True)
  st.metric("Forecasted Demand", "18,500 MT", "Next month (Prophet)")

[col3] st.container(border=True)
  st.metric("Recommended Export", "14,200 MT", "This month")

[col4] st.container(border=True)
  st.metric("Active Alerts", "3", "-2 vs last month", delta_color="inverse")
  st.caption("1 HIGH · 2 MEDIUM")

─── DIVIDER ────────────────────────────────────────────────────────────────

─── 2 COLUMNS (left 55%, right 45%) ────────────────────────────────────────
LEFT: Export Recommendation Panel
  st.subheader("Export Recommendation")
  st.markdown(table with Forecasted Demand / Stock / Safety / Recommended)
  → Use st.markdown() HTML table for clean alignment:
    Forecasted Demand     18,500 MT
    Current Stock         24,221 MT
    Safety Margin          4,300 MT
    ─────────────────────────────
    Recommended Export    14,200 MT   ← highlight row in amber/bold

RIGHT: Recent Anomaly Alerts
  st.subheader("Recent Anomaly Alerts")
  → Show last 3 alerts from anomaly_alerts.json
  → Each row: severity badge + date + type
    [HIGH]  2022-04  Economic Crisis / Fuel Shortage
    [HIGH]  2021-07  Fertiliser Ban — Production Drop
    [MED]   2020-04  COVID-19 Supply Disruption
  st.button("View All Alerts") → sets st.session_state.page-nav hint
    (note: since nav is controlled by sidebar radio, just add a st.info
     "Go to Anomaly Detection in the sidebar to view all alerts.")
```

Severity badge HTML pattern:
```python
def badge(severity: str) -> str:
    cls = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(severity, "badge-low")
    return f'<span class="{cls}">{severity}</span>'

# Usage:
st.markdown(f"{badge('HIGH')} &nbsp; 2022-04 &nbsp; Economic Crisis", unsafe_allow_html=True)
```

---

### `app/views/anomaly.py`

```
HEADER: "Anomaly Detection"
SUBHEADER: "Supply chain disruptions identified by Isolation Forest model"

─── FILTER ROW ─────────────────────────────────────────────────────────────
st.columns([2,2,4])
  col1: st.selectbox("Severity", ["All", "HIGH", "MEDIUM", "LOW"])
  col2: (empty or future date filter)
  col3: st.info("Model: Isolation Forest | Features: export volume, production, FX rate, weather")

─── ALERT TABLE ─────────────────────────────────────────────────────────────
Load anomaly_alerts.json.
Filter by severity if not "All".

For each alert, render a st.container(border=True) row:
  col_badge | col_date | col_type | col_action
  [HIGH]      2022-04    Economic Crisis...  Reduce export targets 20%...

  → Expand arrow (st.expander) shows full description

─── FOOTER INFO ─────────────────────────────────────────────────────────────
st.info("""
Anomaly detection uses scikit-learn Isolation Forest trained on monthly supply
chain indicators (2019–2023): export volume, production, USD/LKR rate, rainfall,
and temperature. Flagged months deviate significantly from the learned normal
distribution.
""")
```

---

### `app/views/blockchain_trace.py`

```
HEADER: "Blockchain Traceability"
SUBHEADER: "Verify tea batch provenance and supply chain integrity"

─── SEARCH FORM ─────────────────────────────────────────────────────────────
st.text_input("Enter Batch ID", placeholder="e.g. TEA001")
st.caption("Available batches: TEA001, TEA002, TEA003")
[Search] button

─── IF BATCH FOUND ──────────────────────────────────────────────────────────
batch_blocks = get_batch(batch_id)   # from blockchain/ledger.py
is_valid = verify_chain(load_ledger())  # full chain verification

st.markdown(f"### Batch: {batch_id}")
validity_html = '<span class="chain-valid">VALID ✓</span>' if is_valid else '<span class="chain-invalid">TAMPERED ✗</span>'
st.markdown(f"Blockchain Status: {validity_html}", unsafe_allow_html=True)

st.divider()

─── STAGE TIMELINE ──────────────────────────────────────────────────────────
For each block in batch_blocks:
  col_icon (width=1) | col_content (width=6) | col_hash (width=3)

  col_icon: "✓" (green color via markdown span)
  col_content:
    **{stage}**
    {location}
    {timestamp}
  col_hash:
    Block #{block_num}
    Hash: {current_hash[:12]}...

  After each block (except last): print vertical line separator
    st.markdown('<div style="margin-left:8px;color:#C8E6C9;font-size:18px;">|</div>', unsafe_allow_html=True)

─── EXPANDER: Raw Block Data ────────────────────────────────────────────────
with st.expander("View raw block data"):
    st.json(batch_blocks)

─── IF BATCH NOT FOUND ──────────────────────────────────────────────────────
st.warning(f"No records found for batch ID '{batch_id}'. Try TEA001, TEA002, or TEA003.")
```

---

## Step 6 — Admin Views

### `app/views/admin_dashboard.py`

```
HEADER: "Admin Dashboard"
SUBHEADER: "System Overview"

─── 4 KPI CARDS ─────────────────────────────────────────────────────────────
[col1] Registered Users     2 (from load_users() count)
[col2] Forecast Model       Trained (check if joblib file exists)
[col3] Blockchain Blocks    13 (from len(load_ledger()))
[col4] Last Model Train     2026-06-16 (from forecast_metrics.json train_start or hardcode)

─── 2 COLUMNS ───────────────────────────────────────────────────────────────
LEFT: Quick Actions
  st.subheader("Quick Actions")
  st.button("Retrain Forecast Model", use_container_width=True)
  st.button("Run Anomaly Detection", use_container_width=True)
  (these buttons show a success toast via st.toast() — no actual retraining needed for demo)

RIGHT: System Status
  st.subheader("System Status")
  st.markdown("""
  | Component         | Status                  |
  |-------------------|------------------------|
  | Forecast Model    | Trained (MAPE: 9.06%)  |
  | Anomaly Model     | Not trained             |
  | Data Pipeline     | 176 months loaded       |
  | Blockchain Ledger | 13 blocks, chain VALID  |
  | Last Updated      | 2026-06-16              |
  """)
```

---

### `app/views/admin_dataset.py`

```
HEADER: "Dataset Management"
SUBHEADER: "Upload and inspect supply chain datasets"

─── UPLOAD SECTION ──────────────────────────────────────────────────────────
st.file_uploader("Upload new dataset", type=["csv", "xlsx"])
st.caption("Accepted formats: CSV (Monthly export data), Excel workbooks")
[note: for demo, uploading shows success message but does not overwrite existing data]

─── DATA PREVIEW ────────────────────────────────────────────────────────────
import pandas as pd
df = pd.read_csv("data/processed/forecast_dataset.csv")
st.subheader("Current Forecast Dataset")
st.caption(f"{len(df)} rows × {len(df.columns)} columns  |  Date range: 2011-10 to 2026-04  |  5 imputed rows")
st.dataframe(df, use_container_width=True, height=400)

─── DATA STATS ──────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1: st.metric("Total Records", "176")
with col2: st.metric("Imputed Rows", "5")
with col3: st.metric("Date Range", "175 months")
```

---

### `app/views/admin_model.py`

```
HEADER: "Model Management"
SUBHEADER: "Train and manage AI forecasting models"

─── 2 COLUMNS ───────────────────────────────────────────────────────────────
LEFT (border container): Forecast Model
  st.subheader("Demand Forecasting — Prophet")
  Status:    Trained
  Algorithm: Prophet (univariate)
  MAPE:      9.06%
  MAE:       1,768 MT
  RMSE:      1,977 MT
  Trained on: 176 months (2011-10 to 2026-04)
  Test period: Last 12 months
  
  [Train Forecast Model]   → disabled (st.button disabled=True), tooltip "Model already trained"
  [Retrain Forecast Model] → on click: st.toast("Retraining started..."); run models.forecasting.main()
                             or just show success toast for demo

RIGHT (border container): Anomaly Detection — Isolation Forest
  st.subheader("Anomaly Detection — Isolation Forest")
  Status:    Not Trained
  Algorithm: Isolation Forest
  Features:  export_mt, production_mt, usd_lkr, rainfall_mm, temp_mean
  Window:    2019-01 to 2023-12 (5 features, ~60 clean months)
  
  [Run Anomaly Detection] → on click: st.toast("Running Isolation Forest..."); 
                            then show success with 5 anomalies found

─── STATUS LOG ──────────────────────────────────────────────────────────────
st.subheader("Action Log")
st.info("Last action: Forecast model trained on 2026-06-16")
```

---

### `app/views/admin_ledger.py`

```
HEADER: "Blockchain Ledger"
SUBHEADER: "Immutable tea batch event ledger (SHA-256 hash chain)"

─── SUMMARY ROW ─────────────────────────────────────────────────────────────
blocks = load_ledger()
is_valid = verify_chain(blocks)

col1, col2, col3 = st.columns(3)
col1: st.metric("Total Blocks", len(blocks))
col2: st.metric("Unique Batches", len(set(b["batch_id"] for b in blocks)))
validity_html = '<span class="chain-valid">VALID ✓</span>' if is_valid else '<span class="chain-invalid">TAMPERED ✗</span>'
col3: st.markdown(f"Chain Status: {validity_html}", unsafe_allow_html=True)

─── LEDGER TABLE ────────────────────────────────────────────────────────────
import pandas as pd
df = pd.DataFrame(blocks)
df["hash_preview"] = df["current_hash"].str[:16] + "..."
df["prev_hash_preview"] = df["previous_hash"].str[:16] + "..."
display_df = df[["block_num","batch_id","stage","location","timestamp","hash_preview"]]
display_df.columns = ["Block #","Batch ID","Stage","Location","Timestamp","Hash (preview)"]
st.dataframe(display_df, use_container_width=True)

─── DIVIDER ─────────────────────────────────────────────────────────────────

─── ADD NEW BATCH EVENT ─────────────────────────────────────────────────────
st.subheader("Add New Batch Event")
with st.form("add_block_form"):
    col1, col2 = st.columns(2)
    with col1:
        batch_id = st.text_input("Batch ID", placeholder="e.g. TEA004")
        stage = st.selectbox("Stage", ["Harvested","Processed","Blended","Packaged","Exported"])
    with col2:
        location = st.text_input("Location", placeholder="e.g. Nuwara Eliya Estate")
        details = st.text_area("Details", placeholder="e.g. 2,000 kg Orthodox Black Tea", height=80)
    submitted = st.form_submit_button("Add to Ledger", use_container_width=True)
    if submitted:
        if batch_id and location and details:
            new_block = add_block(batch_id, stage, location, details)
            st.success(f"Block #{new_block['block_num']} added. Hash: {new_block['current_hash'][:20]}...")
            st.rerun()
        else:
            st.error("Please fill all fields.")
```

---

### `app/views/admin_users.py`

```
HEADER: "User Management"
SUBHEADER: "Manage user accounts and roles"

─── USER TABLE ──────────────────────────────────────────────────────────────
from app.auth import load_users
users_df = load_users()[["username","email","role","created_at"]]
st.dataframe(users_df, use_container_width=True)

─── FORMS (tabs) ────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Add User", "Remove User", "Reset Password"])

[tab1: Add User]
  with st.form("add_user_form"):
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["user", "admin"])
    submitted = st.form_submit_button("Add User")
    if submitted:
      result = auth.add_user(username, email, password, role)
      # show success or error from result

[tab2: Remove User]
  st.warning("Admin accounts cannot be deleted.")
  with st.form("remove_user_form"):
    username = st.text_input("Username to remove")
    confirmed = st.checkbox("I confirm this action is irreversible")
    submitted = st.form_submit_button("Remove User", type="primary")
    if submitted and confirmed:
      # load CSV, filter out username (if not admin), save
      st.success(f"User '{username}' removed.")

[tab3: Reset Password]
  with st.form("reset_pw_form"):
    username = st.text_input("Username")
    new_password = st.text_input("New password", type="password")
    confirm = st.text_input("Confirm password", type="password")
    submitted = st.form_submit_button("Reset Password")
    if submitted:
      if new_password != confirm:
        st.error("Passwords do not match.")
      else:
        # update password hash in CSV
        st.success("Password updated successfully.")
```

> Note: `auth.add_user()` already exists but only accepts `role="user"`. You need to add an optional `role` parameter or handle admin creation separately in admin_users.py.

---

### `app/views/analytics.py`

```
HEADER: "Analytics"
SUBHEADER: "Forecast model performance and export trend analysis"

─── MODEL METRICS (3 cards) ─────────────────────────────────────────────────
Load from models/saved/forecast_metrics.json:
  {mape: 9.06, mae: 1768.0, rmse: 1976.61}

col1: st.metric("Forecast Accuracy (MAPE)", "9.06%", help="Mean Absolute Percentage Error — lower is better. Target: <15%")
col2: st.metric("Mean Absolute Error (MAE)", "1,768 MT", help="Average deviation from actual export volume in metric tonnes")
col3: st.metric("Root Mean Sq Error (RMSE)", "1,977 MT", help="RMSE penalises large errors more than MAE")
(add a st.caption below: "Backtest on last 12 months: May 2025 – Apr 2026")

─── EXPORT TREND CHART ──────────────────────────────────────────────────────
Use the real forecast data + 12-month forecast (call same functions as forecast.py):

from models.forecasting import load_forecast_data, load_model, predict

df = load_forecast_data()
model = load_model()
future_df = predict(model, periods=12)

import plotly.graph_objects as go
fig = go.Figure()

# Historical
hist = future_df[future_df["ds"] <= df["ds"].max()]
fig.add_trace(go.Scatter(x=hist["ds"], y=hist["yhat"], name="Historical (fitted)",
    line=dict(color="#2E7D32", width=2)))

# Forecast
fore = future_df[future_df["ds"] > df["ds"].max()]
fig.add_trace(go.Scatter(x=fore["ds"], y=fore["yhat"], name="Forecast",
    line=dict(color="#4CAF50", width=2, dash="dash")))

# Confidence band
fig.add_trace(go.Scatter(
    x=pd.concat([fore["ds"], fore["ds"][::-1]]),
    y=pd.concat([fore["yhat_upper"], fore["yhat_lower"][::-1]]),
    fill="toself", fillcolor="rgba(46,125,50,0.1)",
    line=dict(color="rgba(0,0,0,0)"), name="90% CI"
))

fig.update_layout(
    title="Monthly Tea Export Volume — Historical & Forecast",
    xaxis_title="Date", yaxis_title="Export Volume (MT)",
    plot_bgcolor="#FFFFFF", paper_bgcolor="#F8FBF8",
    legend=dict(orientation="h", yanchor="bottom", y=1.02)
)
st.plotly_chart(fig, use_container_width=True)

─── FOOTER ──────────────────────────────────────────────────────────────────
st.info("Model: Prophet (univariate). Trained on 176 monthly observations (Oct 2011 – Apr 2026). "
        "Backtest: last 12 months held out. Seasonality: yearly multiplicative. "
        "Changepoint scale: 0.5 (captures 2022 economic crisis trend break).")
```

---

## Step 7 — auth.py Patch (minor)

`auth.add_user()` currently hardcodes `role="user"`. To allow admin to create admin accounts via User Management, add a `role` parameter:

In `app/auth.py`, change `add_user` signature from:
```python
def add_user(username: str, email: str, password: str) -> tuple[bool, str]:
```
to:
```python
def add_user(username: str, email: str, password: str, role: str = "user") -> tuple[bool, str]:
```
And use `role` when building the new row CSV record.

---

## Implementation Sequence (in order)

1. Create `app/style.py`
2. Create `data/anomaly_alerts.json`
3. Create `blockchain/ledger.py` + run it once as script to seed `blockchain_ledger.json`
4. Patch `app/auth.py` — add `role` param to `add_user()`
5. Update `app/main.py` — full role-based routing
6. Create `app/views/user_dashboard.py`
7. Create `app/views/anomaly.py`
8. Create `app/views/blockchain_trace.py`
9. Create `app/views/admin_dashboard.py`
10. Create `app/views/admin_dataset.py`
11. Create `app/views/admin_model.py`
12. Create `app/views/admin_ledger.py`
13. Create `app/views/admin_users.py`
14. Create `app/views/analytics.py`

**Run after each major step:** `.venv/Scripts/python.exe -m streamlit run app/main.py`

---

## Demo Script (Friday)

| Step | Action | Shows |
|------|--------|-------|
| 1 | Open app → landing page | Public landing, Login/Register buttons |
| 2 | Register new user → login as user | User sidebar nav (4 items) |
| 3 | Dashboard page | 4 KPI cards, export recommendation, anomaly summary |
| 4 | Forecasting page | Real Prophet chart, 12-month forecast |
| 5 | Anomaly Detection | 5 alerts with HIGH/MEDIUM badges |
| 6 | Blockchain Traceability | Search TEA001 → 5-stage timeline, VALID ✓ |
| 7 | Log out → log in as admin/admin123 | Admin sidebar nav (6 items) |
| 8 | Admin Dashboard | System status, quick actions |
| 9 | Blockchain Ledger | 13 blocks table, add new batch event |
| 10 | User Management | Add new user, see table |
| 11 | Analytics | MAPE 9.06%, export trend chart |

---

## Verification Checklist

- [ ] `streamlit run app/main.py` — starts without import error
- [ ] Login as `admin` / `admin123` → sees 6-item admin sidebar
- [ ] Login as regular user → sees 4-item user sidebar
- [ ] User Dashboard: 4 metric cards render
- [ ] Forecasting: Prophet chart renders (real data)
- [ ] Anomaly Detection: 5 alert rows with severity badges
- [ ] Blockchain Traceability: search TEA001 → 5 stages + VALID
- [ ] Admin Blockchain Ledger: 13-block table + add form works
- [ ] Admin User Management: user list renders + add form works
- [ ] Admin Analytics: 3 metric cards + Plotly chart renders
- [ ] Sign out → returns to landing page
