# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of RCD² seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### **DO NOT report security vulnerabilities through public GitHub issues.**

### Reporting Process

1. Please email `security@rcd2-project.local` (mock email) or contact the maintainers directly.
2. Provide a detailed description of the vulnerability, including:
   - Steps to reproduce
   - Potential impact
   - Affected components
3. We will acknowledge your report within 48 hours.
4. We will investigate the issue and keep you updated on our progress.
5. Once resolved, we will issue a patch and credit you (if desired) in our release notes.

## Security Features

RCD² includes several security features by design:

- **Sandboxed Execution**: Auto-retraining runs in isolated environments (when deployed via Docker).
- **Input Validation**: All API endpoints use Pydantic models for strict type checking and validation.
- **No External Calls**: The system is designed to run locally without unauthorized external network requests.
- **Audit Logging**: Critical actions (model promotion, rollback, retraining) are logged to immutable audit trails.
- **Model Integrity**: SHA256 checksums verify model artifacts have not been tampered with.

## Responsible AI & Safety

This project adheres to Responsible AI principles:
- **Fairness**: Includes metrics to detect bias in model predictions.
- **Transparency**: Provides explainability metrics (SHAP-like) for drift and predictions.
- **Privacy**: Designed to work with anonymized or synthetic data.

## Disclaimer

This software is provided "as is" without warranty of any kind. Users are responsible for ensuring their deployment meets their specific security and compliance requirements (ISO 27001, SOC 2, etc.).
