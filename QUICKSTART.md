# 🚀 Quick Start Guide

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

## Installation

```bash
# Navigate to project directory
cd rcd2

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Platform

### Start the Backend

```bash
# From project root
RCD2_API_KEY=dev-key-123 python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Basic Usage

### 1. View the Dashboard

Navigate to http://localhost:8000/dashboard to see:
- Real-time drift scores
- Model performance metrics
- Retraining history
- Live charts

### 2. Test Predictions

```python
import requests

# Make a prediction
response = requests.post(
    "http://localhost:8000/api/predict",
    json={"features": [0.5, -0.3, 1.2]},
    headers={"X-API-Key": "dev-key-123"}
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['probability']}")
print(f"Model Version: {result['model_version']}")
```

### 3. Ingest Streaming Data

```python
# Ingest a data point
requests.post(
    "http://localhost:8000/api/ingest",
    json={
        "features": [0.5, -0.3, 1.2],
        "label": 1
    },
    headers={"X-API-Key": "dev-key-123"}
)
```

### 4. Check for Drift

```python
# Get drift status
response = requests.get("http://localhost:8000/api/drift", headers={"X-API-Key": "dev-key-123"})
drift = response.json()

print(f"Drift Score: {drift['drift_score']}")
print(f"Severity: {drift['severity']}")
print(f"Type: {drift['drift_type']}")
```

### 5. Trigger Retraining

```python
# Force retraining
response = requests.post(
    "http://localhost:8000/api/force_retrain",
    json={
        "drift_score": 75.0,
        "reason": "manual_trigger"
    },
    headers={"X-API-Key": "dev-key-123"}
)

result = response.json()
if result['success']:
    print(f"New model: {result['version']}")
    print(f"Promoted: {result['promoted']}")
    print(f"Improvement: {result['improvement']:.2%}")
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_drift.py -v
```

## Monitoring

### Key Metrics

- **Drift Score**: 0-100 scale indicating distribution shift
  - < 20: No drift
  - 20-40: Low drift
  - 40-70: Moderate drift
  - 70+: High drift (triggers retraining)

- **Severity Levels**:
  - `none`: No action needed
  - `low`: Monitor closely
  - `moderate`: Schedule retraining
  - `high`: Immediate retraining triggered

### Auto-Retraining Triggers

1. **Drift Threshold**: drift_score >= 70
2. **Accuracy SLA**: accuracy < 0.85
3. **Model Age**: > 30 days (configurable)

## Troubleshooting

### Issue: "No models found"

**Solution**: Wait a few seconds for initial model training to complete, or manually trigger:

```python
from backend.engines.retrain_engine import RetrainEngine
engine = RetrainEngine()
engine.train_initial_model()
```

### Issue: "Insufficient data for drift detection"

**Solution**: Ingest at least 30 samples before drift detection becomes meaningful.

### Issue: Port 8000 already in use

**Solution**: Use a different port:

```bash
uvicorn backend.main:app --port 8001
```

## Next Steps

1. **Customize Configuration**: Edit thresholds in `backend/engines/retrain_engine.py`
2. **Add Real Data**: Replace synthetic data with your actual data streams
3. **Enhance Monitoring**: Integrate with external monitoring tools (Prometheus, Grafana)
4. **Production Deployment**: Use gunicorn or similar WSGI server
5. **Database Integration**: Add PostgreSQL for persistence

## API Documentation

Full API documentation available at http://localhost:8000/docs after starting the server.

## Support

For issues, check:
1. Logs in `/logs`
2. Audit trail in `/logs/audit`
3. API documentation at `/docs`
