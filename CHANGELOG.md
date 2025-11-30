# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-11-30

### Fixed
- **CI/CD**: Resolved GitHub Actions failures by setting `RCD2_API_KEY` in test environment.
- **Linting**: Fixed all `mypy` type errors and `flake8` warnings.
- **Security**:
  - Implemented API Key authentication (`X-API-Key`) for all sensitive endpoints.
  - Added constant-time key comparison to prevent timing attacks.
  - Updated `QUICKSTART.md` and `README.md` with security instructions.
- **Documentation**:
  - Fixed broken links and emojis in `README.md`.
  - Updated repository URLs to point to the correct location.
  - Corrected Python examples in `QUICKSTART.md` to include authentication headers.

## [1.0.0] - 2024-01-01

### Added
- **Drift Detection Engine**:
  - ADWIN (Adaptive Windowing) implementation
  - Statistical tests: PSI, KS Test, KL Divergence, JS Divergence
  - Multi-dimensional analysis (Data, Concept, Prediction drift)
- **Auto-Retraining Pipeline**:
  - Automated trigger logic (Drift Score > 70, Accuracy < 0.85)
  - Sandboxed training execution
  - Validation suite (Performance, Explainability, Fairness, Stability)
- **Model Registry**:
  - Version control with SHA256 checksums
  - Metadata tracking and audit logging
  - Rollback and promotion capabilities
- **API & Backend**:
  - FastAPI implementation with 8 core endpoints
  - Async request handling
  - Structured logging (JSONL)
- **Frontend**:
  - Real-time monitoring dashboard
  - Interactive charts (Chart.js)
  - Dark mode UI
- **Documentation**:
  - Comprehensive Architecture overview
  - API documentation (Swagger/Redoc)
  - Quick start and contribution guides

### Security
- Implemented input validation via Pydantic
- Added model integrity verification
- Established audit trail for all governance actions
