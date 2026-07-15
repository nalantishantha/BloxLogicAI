# BloxLogicAI — Requirements & Deliverables

Reference companion to `CLAUDE.md`. Captures the dissertation scope, functional and
non-functional requirements, acceptance criteria, and the deliverables checklist.
Source of record: `FINAL_PROJECT_PROPOSAL_33_160.pdf`.

---

## 1. Problem statement

Sri Lanka's tea industry — a major export earner — suffers from poor demand
visibility, unmanaged supply-chain disruptions (e.g. COVID-19 2020, the 2022 fuel
& fertiliser crisis), and a lack of trustworthy batch traceability. BloxLogicAI
addresses these with one lightweight, offline-capable system combining demand
**forecasting**, disruption **anomaly detection**, and blockchain **traceability**.

## 2. Aim & objectives

**Aim:** Build an AI- and blockchain-enabled prototype that forecasts tea export
demand, detects supply-chain anomalies, and provides immutable batch traceability,
delivered through a single web dashboard.

**Objectives**
1. Collect and clean real Sri Lankan tea export/production/macro data.
2. Build and validate a monthly export-volume forecasting model (Prophet).
3. Build and validate an anomaly-detection model (Isolation Forest).
4. Implement a SHA-256 blockchain ledger for tea-batch lifecycle traceability.
5. Integrate all three into a Streamlit dashboard (user + admin views).
6. Test, document, and evaluate against the acceptance criteria below.

---

## 3. Functional requirements

| ID | Requirement | Module | Status |
|----|-------------|--------|--------|
| FR1 | Ingest & clean real export/production/macro/weather data into model-ready datasets | Data | ✅ |
| FR2 | Forecast monthly tea export volume for a user-chosen horizon (3–24 months) | Forecasting | ✅ |
| FR3 | Show forecast with confidence interval and backtest accuracy metrics | Forecasting | ✅ |
| FR4 | Allow model retrain on demand from the UI | Forecasting | ✅ |
| FR5 | Export forecast results to CSV | Forecasting | ✅ |
| FR6 | Detect & flag anomalous months/periods in supply-chain indicators | Anomaly | ⏳ |
| FR7 | Visualise anomalies against historical context | Anomaly | 🔲 |
| FR8 | Register a tea batch (harvest → processing → export) on a hash chain | Blockchain | ✅ |
| FR9 | Verify ledger integrity (detect tampering) | Blockchain | ✅ |
| FR10 | Generate a QR code per batch for traceability lookup | Blockchain | ✅ |
| FR11 | Single dashboard with user portal + admin portal | UI | 🔲 (forecast view done) |

## 4. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR1 | Runs locally, offline, no DB/cloud | `streamlit run app/main.py` only |
| NFR2 | Forecast accuracy | MAPE ≤ 15% on 12-month hold-out (**achieved 9.06%**) |
| NFR3 | Reproducibility | pinned `requirements.txt`; committed model + processed data |
| NFR4 | Usability | non-technical user can run a forecast in ≤ 3 clicks |
| NFR5 | Maintainability | modular pipeline, unit tests, documented code |
| NFR6 | Performance | dashboard interaction < 3 s with cached model |
| NFR7 | Integrity | blockchain tamper-evident via linked SHA-256 hashes |

---

## 5. Acceptance criteria

- **Forecasting:** backtest MAPE within target; forecast + CI render; retrain & CSV export work. ✅
- **Anomaly:** model flags known disruption periods (2020 COVID, 2022 crisis) as anomalies; results visualised.
- **Blockchain:** batches append immutably; any edit to a block breaks verification; QR resolves to a batch.
- **Integration:** all three reachable from one Streamlit app; tests pass; docs complete.

## 6. Deliverables checklist

- [x] Cleaned datasets + reproducible data pipeline (`utils/data_loader.py`)
- [x] Forecasting model + tests + saved artifacts + metrics
- [x] Forecasting dashboard (Streamlit)
- [ ] Anomaly-detection model + tests + visualisation
- [x] Blockchain ledger module + QR generation + tests
- [ ] Integrated dashboard (user + admin portals)
- [ ] Architecture diagram & user manual (`docs/`)
- [ ] Final dissertation report + demo
- [ ] Source code pushed to GitHub by 2026-06-29

## 7. Evaluation method

- **Quantitative:** forecast error (MAE/RMSE/MAPE on hold-out); anomaly
  detection against labelled known-disruption months; blockchain
  tamper-detection test.
- **Qualitative:** usability walkthrough of the dashboard against the
  3-click usability target.

## 8. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Sparse/dirty source data | reconcile to official annual totals; interpolate & flag gaps |
| Prophet/cmdstan env breakage on Windows | pin `cmdstanpy==1.2.4` (documented in CLAUDE.md) |
| Scope creep across 3 modules in 21 days | strict build-one-module-fully-then-next order |
| Anomaly window too short (features only 2019–2023) | accept reduced window; treat as prototype, document limitation |

---

*See `CLAUDE.md` for environment, commands, data details, and current build state.*
