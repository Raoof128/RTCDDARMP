"""
Main Drift Detection Engine
Orchestrates all drift detection methods and provides unified interface
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from backend.engines.adwin import ADWIN
from backend.engines.stat_tests import (
    kl_divergence,
    kolmogorov_smirnov_test,
    population_stability_index,
)
from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DriftDetector:
    """
    Unified drift detection engine combining multiple algorithms.

    Detects:
    - Data Drift (feature distribution changes)
    - Concept Drift (target relationship changes)
    - Prediction Drift (model output changes)
    - Covariate Shift (input distribution without target change)
    """

    def __init__(self, n_features: int = 3):
        self.n_features = n_features

        # Reference distributions (baseline)
        self.reference_features: Optional[np.ndarray] = None
        self.reference_labels: Optional[np.ndarray] = None
        self.reference_predictions: Optional[np.ndarray] = None

        # Current window
        self.current_features: List[np.ndarray] = []
        self.current_labels: List[float] = []
        self.current_predictions: List[float] = []

        # Streaming detectors (one per feature + one for predictions)
        self.adwin_detectors = [ADWIN(delta=0.002) for _ in range(n_features + 1)]

        # Configuration
        self.window_size = 100
        self.drift_threshold = 0.2  # For PSI

        # Drift history
        self.drift_history: List[Dict] = []

    def set_reference(
        self,
        features: np.ndarray,
        labels: Optional[np.ndarray] = None,
        predictions: Optional[np.ndarray] = None,
    ):
        """
        Set reference (baseline) distributions.

        Parameters:
        -----------
        features : np.ndarray
            Reference feature matrix (n_samples, n_features)
        labels : np.ndarray, optional
            Reference labels
        predictions : np.ndarray, optional
            Reference predictions
        """
        self.reference_features = features
        self.reference_labels = labels
        self.reference_predictions = predictions
        logger.info(f"Reference set with {len(features)} samples")

    def add_sample(
        self,
        features: np.ndarray,
        label: Optional[float] = None,
        prediction: Optional[float] = None,
        error: float = 0.0,
    ):
        """
        Add new sample to current window.

        Parameters:
        -----------
        features : np.ndarray
            Feature vector
        label : float, optional
            True label
        prediction : float, optional
            Model prediction
        error : float
            Prediction error (1 if incorrect, 0 if correct)
        """
        self.current_features.append(features)
        if label is not None:
            self.current_labels.append(label)
        if prediction is not None:
            self.current_predictions.append(prediction)

        # Update ADWIN detectors
        for i, feature_val in enumerate(features):
            self.adwin_detectors[i].add_element(feature_val)

        # Add error to last ADWIN (for prediction drift)
        self.adwin_detectors[-1].add_element(error)

        # Maintain window size
        if len(self.current_features) > self.window_size:
            self.current_features.pop(0)
            if self.current_labels:
                self.current_labels.pop(0)
            if self.current_predictions:
                self.current_predictions.pop(0)

    def detect_drift(self) -> Dict[str, Any]:
        """
        Detect drift using all available methods.

        Returns:
        --------
        Dict containing:
            - drift_score: 0-100 score
            - drift_type: type of drift detected
            - severity: low/moderate/high
            - affected_features: list of drifted features
            - details: detailed metrics
        """
        if self.reference_features is None:
            return {
                "drift_score": 0,
                "drift_type": "none",
                "severity": "none",
                "affected_features": [],
                "details": {"error": "No reference distribution set"},
            }

        if len(self.current_features) < 30:  # Need minimum samples
            return {
                "drift_score": 0,
                "drift_type": "none",
                "severity": "insufficient_data",
                "affected_features": [],
                "details": {"current_samples": len(self.current_features)},
            }

        # Convert current window to array
        current_features_array = np.array(self.current_features)

        # Initialize results
        # Initialize results
        drift_scores: List[float] = []
        affected_features: List[int] = []
        details: Dict[str, Any] = {}

        # 1. Feature-wise drift detection
        feature_drifts = []
        for i in range(self.n_features):
            ref_feature = self.reference_features[:, i]
            curr_feature = current_features_array[:, i]

            # PSI
            psi = population_stability_index(ref_feature, curr_feature)

            # KS test
            ks_stat, ks_pval, ks_drift = kolmogorov_smirnov_test(
                ref_feature, curr_feature
            )

            # KL divergence
            kl_div = kl_divergence(ref_feature, curr_feature)

            # ADWIN
            adwin_drift = self.adwin_detectors[i].drift_detected

            # Aggregate feature drift score
            feature_score = (
                (psi / 0.2) * 25
                + ks_stat * 25  # PSI contribution
                + min(kl_div, 1.0) * 25  # KS contribution
                + (1.0 if adwin_drift else 0.0)  # KL contribution
                * 25  # ADWIN contribution
            )

            feature_drifts.append(
                {
                    "feature_index": i,
                    "psi": float(psi),
                    "ks_statistic": float(ks_stat),
                    "ks_pvalue": float(ks_pval),
                    "kl_divergence": float(kl_div),
                    "adwin_drift": adwin_drift,
                    "drift_score": float(feature_score),
                }
            )

            if psi > self.drift_threshold or ks_drift or adwin_drift:
                affected_features.append(i)
                drift_scores.append(feature_score)

        details["feature_drift"] = feature_drifts

        # 2. Prediction drift (if available)
        if self.reference_predictions is not None and len(self.current_predictions) > 0:
            curr_predictions = np.array(self.current_predictions)

            psi_pred = population_stability_index(
                self.reference_predictions, curr_predictions
            )

            ks_stat_pred, _, _ = kolmogorov_smirnov_test(
                self.reference_predictions, curr_predictions
            )

            prediction_drift_score = (psi_pred / 0.2) * 50 + ks_stat_pred * 50
            drift_scores.append(prediction_drift_score)

            details["prediction_drift"] = {
                "psi": float(psi_pred),
                "ks_statistic": float(ks_stat_pred),
                "drift_score": float(prediction_drift_score),
            }

        # 3. Concept drift (if labels available)
        if self.reference_labels is not None and len(self.current_labels) > 0:
            curr_labels = np.array(self.current_labels)

            # Compare label distributions
            psi_label = population_stability_index(self.reference_labels, curr_labels)

            concept_drift_score = (psi_label / 0.2) * 100
            drift_scores.append(concept_drift_score)

            details["concept_drift"] = {
                "psi": float(psi_label),
                "drift_score": float(concept_drift_score),
            }

        # Calculate overall drift score
        overall_drift_score = float(np.mean(drift_scores)) if drift_scores else 0.0
        overall_drift_score = float(
            min(100.0, max(0.0, overall_drift_score))
        )  # Clamp 0-100

        # Determine drift type and severity
        drift_type = str(self._classify_drift_type(details, affected_features))
        severity = str(self._classify_severity(overall_drift_score))

        result = {
            "drift_score": overall_drift_score,
            "drift_type": drift_type,
            "severity": severity,
            "affected_features": affected_features,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommended_action": self._get_recommendation(
                overall_drift_score, severity
            ),
        }

        # Log to history
        self.drift_history.append(result)

        logger.info(
            f"Drift detected: score={overall_drift_score:.2f}, type={drift_type}, severity={severity}"
        )

        return convert_numpy_types(result)  # type: ignore

    def _classify_drift_type(self, details: Dict, affected_features: List[int]) -> str:
        """Classify the type of drift"""
        if len(affected_features) > 0:
            if "concept_drift" in details and details["concept_drift"]["psi"] > 0.2:
                return "concept_drift"
            elif (
                "prediction_drift" in details
                and details["prediction_drift"]["psi"] > 0.2
            ):
                return "prediction_drift"
            else:
                return "data_drift"
        return "none"

    def _classify_severity(self, drift_score: float) -> str:
        """Classify drift severity"""
        if drift_score >= 70:
            return "high"
        elif drift_score >= 40:
            return "moderate"
        elif drift_score >= 20:
            return "low"
        else:
            return "none"

    def _get_recommendation(self, drift_score: float, severity: str) -> str:
        """Get recommended action based on drift"""
        if severity == "high":
            return "URGENT: Trigger immediate retraining"
        elif severity == "moderate":
            return "Schedule retraining within 24 hours"
        elif severity == "low":
            return "Monitor closely, consider retraining if persists"
        else:
            return "No action required"

    def get_drift_history(self, limit: int = 10) -> List[Dict]:
        """Get recent drift history"""
        return self.drift_history[-limit:]

    def reset(self):
        """Reset detector state"""
        self.current_features = []
        self.current_labels = []
        self.current_predictions = []
        for detector in self.adwin_detectors:
            detector.reset()
        logger.info("Drift detector reset")
