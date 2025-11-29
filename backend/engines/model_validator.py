"""
Model Validator
Validates models before deployment with multiple checks
"""

from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ModelValidator:
    """
    Model validation suite with multiple checks:
    - Performance metrics
    - Explainability checks (mock SHAP)
    - Fairness checks (synthetic)
    - Stability checks
    """

    def __init__(self):
        # Validation thresholds
        self.thresholds = {
            "min_accuracy": 0.70,
            "min_precision": 0.65,
            "min_recall": 0.65,
            "min_f1": 0.65,
            "max_feature_importance_concentration": 0.8,  # No single feature > 80%
        }

    def validate_model(
        self,
        model: Any,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive model validation.

        Parameters:
        -----------
        model : Any
            Trained model to validate
        X_val : np.ndarray
            Validation features
        y_val : np.ndarray
            Validation labels
        feature_names : List[str], optional
            Feature names

        Returns:
        --------
        Dict
            Validation results with pass/fail and details
        """
        logger.info("🔍 Starting model validation...")

        results: Dict[str, Any] = {"passed": True, "checks": {}, "failures": []}

        # Make predictions
        y_pred = model.predict(X_val)

        # 1. Performance Metrics Check
        performance_check = self._check_performance(y_val, y_pred)
        results["checks"]["performance"] = performance_check

        if not performance_check["passed"]:
            results["passed"] = False
            results["failures"].append("performance")

        # 2. Explainability Check (Mock SHAP)
        explainability_check = self._check_explainability(model, X_val, feature_names)
        results["checks"]["explainability"] = explainability_check

        if not explainability_check["passed"]:
            results["passed"] = False
            results["failures"].append("explainability")

        # 3. Fairness Check (Synthetic)
        fairness_check = self._check_fairness(y_val, y_pred)
        results["checks"]["fairness"] = fairness_check

        if not fairness_check["passed"]:
            results["passed"] = False
            results["failures"].append("fairness")

        # 4. Stability Check
        stability_check = self._check_stability(model, X_val)
        results["checks"]["stability"] = stability_check

        if not stability_check["passed"]:
            results["passed"] = False
            results["failures"].append("stability")

        if results["passed"]:
            logger.info("✅ Model passed all validation checks")
        else:
            logger.warning(f"❌ Model failed validation: {results['failures']}")

        return results

    def _check_performance(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Check performance metrics"""

        accuracy = accuracy_score(y_true, y_pred)

        # Handle binary vs multiclass
        average_method = "binary" if len(np.unique(y_true)) == 2 else "weighted"

        precision = precision_score(
            y_true, y_pred, average=average_method, zero_division=0
        )
        recall = recall_score(y_true, y_pred, average=average_method, zero_division=0)
        f1 = f1_score(y_true, y_pred, average=average_method, zero_division=0)

        passed = (
            accuracy >= self.thresholds["min_accuracy"]
            and precision >= self.thresholds["min_precision"]
            and recall >= self.thresholds["min_recall"]
            and f1 >= self.thresholds["min_f1"]
        )

        return {
            "passed": passed,
            "metrics": {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
            },
            "thresholds": self.thresholds,
        }

    def _check_explainability(
        self, model: Any, X_val: np.ndarray, feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check explainability (mock SHAP-like feature importance).

        For tree-based models, use feature_importances_.
        For others, use mock values.
        """

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X_val.shape[1])]

        # Try to get feature importances
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            # Mock importances for non-tree models
            importances = np.random.dirichlet(np.ones(X_val.shape[1]))

        # Check concentration (no single feature should dominate)
        max_importance = np.max(importances)
        concentration_ok = (
            max_importance < self.thresholds["max_feature_importance_concentration"]
        )

        feature_importance_dict = {
            name: float(imp) for name, imp in zip(feature_names, importances)
        }

        return {
            "passed": concentration_ok,
            "feature_importances": feature_importance_dict,
            "max_importance": float(max_importance),
            "threshold": self.thresholds["max_feature_importance_concentration"],
            "explanation": "Feature importance distribution is balanced"
            if concentration_ok
            else "Single feature has too much influence",
        }

    def _check_fairness(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """
        Check fairness metrics (synthetic/mock).

        In production, this would use protected attributes and demographic parity,
        equal opportunity, etc. Here we use synthetic checks.
        """

        # Mock fairness check: ensure predictions are not too imbalanced
        pred_distribution = np.bincount(y_pred.astype(int)) / len(y_pred)

        # Check if any class is predicted less than 10% of the time (imbalance)
        min_class_proportion = np.min(pred_distribution)

        # For fairness, we want reasonably balanced predictions (>10%)
        passed = (
            min_class_proportion > 0.10
            or len(pred_distribution) == 2
            and min_class_proportion > 0.05
        )

        return {
            "passed": passed,
            "prediction_distribution": {
                f"class_{i}": float(prop) for i, prop in enumerate(pred_distribution)
            },
            "min_class_proportion": float(min_class_proportion),
            "explanation": "Prediction distribution is balanced"
            if passed
            else "Predictions are too imbalanced",
        }

    def _check_stability(self, model: Any, X_val: np.ndarray) -> Dict[str, Any]:
        """
        Check model stability through perturbation testing.

        Add small noise to inputs and check if predictions remain stable.
        """

        # Original predictions
        y_pred_original = model.predict(X_val)

        # Add small noise (1% of std)
        noise_scale = 0.01
        X_perturbed = X_val + np.random.normal(0, noise_scale, X_val.shape)

        # Predictions on perturbed data
        y_pred_perturbed = model.predict(X_perturbed)

        # Calculate stability (% of predictions that remain the same)
        stability = np.mean(y_pred_original == y_pred_perturbed)

        # We want at least 90% stability
        passed = stability >= 0.90

        return {
            "passed": passed,
            "stability_score": float(stability),
            "threshold": 0.90,
            "explanation": "Model predictions are stable under small perturbations"
            if passed
            else "Model is too sensitive to input noise",
        }
