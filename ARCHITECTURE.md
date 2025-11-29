# RCD² System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT / USER INTERFACE                         │
│                                                                          │
│  ┌──────────────────────┐        ┌──────────────────────────────────┐  │
│  │   Web Dashboard      │        │   API Clients (SDK/cURL)         │  │
│  │   (HTML/CSS/JS)      │        │   (Python, REST, etc.)           │  │
│  └──────────┬───────────┘        └──────────────┬───────────────────┘  │
└─────────────┼──────────────────────────────────┼──────────────────────┘
              │                                    │
              │   HTTP/WebSocket                   │   HTTP/REST
              │                                    │
┌─────────────▼────────────────────────────────────▼──────────────────────┐
│                         FASTAPI BACKEND LAYER                            │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  /predict    │  │  /ingest     │  │  /drift      │  │  /retrain  │ │
│  │  endpoint    │  │  endpoint    │  │  endpoint    │  │  endpoint  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                  │                 │        │
│  ┌──────┴─────────────────┴──────────────────┴─────────────────┴──────┐ │
│  │                     API ROUTER MIDDLEWARE                           │ │
│  │               (CORS, Auth, Logging, Validation)                     │ │
│  └──────┬──────────────────────────────────────────────────────────┬──┘ │
└─────────┼──────────────────────────────────────────────────────────┼────┘
          │                                                           │
          ▼                                                           ▼
┌─────────────────────────────────────┐  ┌──────────────────────────────────┐
│      DRIFT DETECTION ENGINE         │  │    AUTO-RETRAINING ENGINE        │
│                                     │  │                                  │
│  ┌────────────────────────────────┐ │  │  ┌────────────────────────────┐ │
│  │  Statistical Tests             │ │  │  │  Training Window Extractor │ │
│  │  - PSI (Pop. Stability Index)  │ │  │  │  - Sliding window          │ │
│  │  - KS Test (Kolmogorov-Smirnov)│ │  │  │  - Sample aggregation      │ │
│  │  - KL Divergence               │ │  │  └────────────┬───────────────┘ │
│  │  - JS Divergence               │ │  │               │                 │
│  │  - Wasserstein Distance        │ │  │  ┌────────────▼───────────────┐ │
│  └────────────┬───────────────────┘ │  │  │  Model Trainer             │ │
│               │                     │  │  │  - RandomForest/Custom     │ │
│  ┌────────────▼───────────────────┐ │  │  │  - Hyperparameter config   │ │
│  │  Streaming Detectors           │ │  │  └────────────┬───────────────┘ │
│  │  - ADWIN (Adaptive Windowing)  │ │  │               │                 │
│  │  - DDM (Drift Detection Method)│ │  │  ┌────────────▼───────────────┐ │
│  │  - EDDM (Early DDM)            │ │  │  │  Model Validator           │ │
│  └────────────┬───────────────────┘ │  │  │  - Performance checks      │ │
│               │                     │  │  │  - Explainability (SHAP)   │ │
│  ┌────────────▼───────────────────┐ │  │  │  - Fairness metrics        │ │
│  │  Multi-Dimensional Analysis    │ │  │  │  - Stability testing       │ │
│  │  - Data Drift                  │ │  │  └────────────┬───────────────┘ │
│  │  - Concept Drift               │ │  │               │                 │
│  │  - Prediction Drift            │ │  │  ┌────────────▼───────────────┐ │
│  │  - Covariate Shift             │ │  │  │  Promotion Decision        │ │
│  └────────────┬───────────────────┘ │  │  │  - Compare with champion   │ │
│               │                     │  │  │  - Improvement threshold   │ │
│  ┌────────────▼───────────────────┐ │  │  │  - Auto-promote if better  │ │
│  │  Drift Scoring & Classification│ │  │  └────────────┬───────────────┘ │
│  │  - Score: 0-100                │ │  │               │                 │
│  │  - Severity: none/low/mod/high │ │  └───────────────┼─────────────────┘
│  │  - Type: data/concept/pred     │ │                  │
│  │  - Recommendations             │ │                  │
│  └────────────────────────────────┘ │                  │
└─────────────┬───────────────────────┘                  │
              │                                           │
              │                                           │
       Drift Alert/Trigger                                │
              │                                           │
              └───────────────────┬───────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────────────┐
        │                  MODEL REGISTRY & VERSIONING             │
        │                                                          │
        │  ┌──────────────────────────────────────────────────┐  │
        │  │  Model Version Control                           │  │
        │  │  - Semantic versioning (v{timestamp})            │  │
        │  │  - Git-like tracking                             │  │
        │  └──────────────┬───────────────────────────────────┘  │
        │                 │                                       │
        │  ┌──────────────▼───────────────────────────────────┐  │
        │  │  Metadata Store                                  │  │
        │  │  - Model type, accuracy, drift_score             │  │
        │  │  - Training/validation samples                   │  │
        │  │  - Hyperparameters, feature names                │  │
        │  │  - Timestamps, notes                             │  │
        │  └──────────────┬───────────────────────────────────┘  │
        │                 │                                       │
        │  ┌──────────────▼───────────────────────────────────┐  │
        │  │  Checksum & Integrity                            │  │
        │  │  - SHA256 hash verification                      │  │
        │  │  - Corruption detection                          │  │
        │  └──────────────┬───────────────────────────────────┘  │
        │                 │                                       │
        │  ┌──────────────▼───────────────────────────────────┐  │
        │  │  Champion Model Tracking                         │  │
        │  │  - Currently deployed model                      │  │
        │  │  - Promotion flags                               │  │
        │  └──────────────┬───────────────────────────────────┘  │
        │                 │                                       │
        │  ┌──────────────▼───────────────────────────────────┐  │
        │  │  Rollback & Recovery                             │  │
        │  │  - Instant rollback to previous version          │  │
        │  │  - Emergency recovery procedures                 │  │
        │  └──────────────────────────────────────────────────┘  │
        └────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────────────────────┐
        │            AUDIT TRAIL & GOVERNANCE LAYER                │
        │                                                          │
        │  ┌──────────────────────────────────────────────────┐  │
        │  │  Structured Logging                              │  │
        │  │  - All API calls, predictions, ingestions        │  │
        │  │  - Model training/retraining events              │  │
        │  │  - Drift detection results                       │  │
        │  └──────────────┬───────────────────────────────────┘  │
        │                 │                                       │
        │  ┌──────────────▼───────────────────────────────────┐  │
        │  │  Compliance Mappings                             │  │
        │  │  - ISO/IEC 42001 (AI Management System)          │  │
        │  │  - NIST AI RMF (Risk Management Framework)       │  │
        │  │  - OAIC ADM (Automated Decision-Making)          │  │
        │  └──────────────┬───────────────────────────────────┘  │
        │                 │                                       │
        │  ┌──────────────▼───────────────────────────────────┐  │
        │  │  Alert & Notification System                     │  │
        │  │  - Email/webhook alerts (mock)                   │  │
        │  │  - Threshold-based triggers                      │  │
        │  │  - SLA monitoring                                │  │
        │  └──────────────────────────────────────────────────┘  │
        └──────────────────────────────────────────────────────────┘


        ┌─────────────────────────────────────────────────────────┐
        │                  DATA STORAGE LAYER                      │
        │                                                          │
        │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
        │  │   models/    │  │    logs/     │  │    data/     │  │
        │  │  (pickled)   │  │   (JSONL)    │  │  (streams)   │  │
        │  └──────────────┘  └──────────────┘  └──────────────┘  │
        └──────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Prediction Flow
```
User Request → /predict endpoint → Load Champion Model → 
Predict → Return (prediction + confidence + version)
```

### 2. Ingestion & Drift Monitoring Flow
```
Data Stream → /ingest endpoint → Add to Drift Detector Window →
Update ADWIN → Check if enough samples → Calculate Drift Metrics →
Return drift status
```

### 3. Auto-Retraining Flow
```
Drift Detected (score > 70) OR Accuracy Drop → Trigger Retraining →
Extract Training Window → Train New Model → Validate (4 checks) →
Compare with Champion → Promote if Better → Update Registry →
Log to Audit Trail
```

### 4. Model Registry Flow
```
Register Model → Calculate Checksum → Store Metadata →
Serialize Model → Save to Disk → Update Registry JSON →
Log Audit Event
```

## Component Interactions

```
┌─────────────┐
│ Dashboard   │────┐
└─────────────┘    │
                   │ (Polls every 30s)
┌─────────────┐    │
│ API Client  │────┼──────────┐
└─────────────┘    │          │
                   ▼          ▼
              ┌─────────────────────┐
              │   FastAPI Routes    │
              └──────┬──────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │  Drift  │  │ Retrain │  │  Model  │
  │ Detector│  │ Engine  │  │Registry │
  └────┬────┘  └────┬────┘  └────┬────┘
       │            │            │
       └────────────┼────────────┘
                    │
                    ▼
             ┌─────────────┐
             │ Audit Logger│
             └─────────────┘
```

## Technology Stack

- **Backend**: Python 3.9+, FastAPI, Uvicorn
- **ML Framework**: scikit-learn, NumPy, Pandas
- **Statistics**: SciPy
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Testing**: pytest, pytest-cov
- **Logging**: structlog
- **Code Quality**: black, flake8, mypy, isort

## Security & Compliance

- ✅ No external data connections (sandbox mode)
- ✅ Checksum verification for model integrity
- ✅ Full audit trail (JSONL format)
- ✅ Configurable access controls
- ✅ Safe rollback mechanisms
- ✅ Synthetic data only (privacy-safe)
