"""
Auto-Retraining Engine
Handles automated model retraining, validation, and deployment
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from backend.engines.model_registry import ModelMetadata, ModelRegistry
from backend.engines.model_validator import ModelValidator
from backend.utils.data_stream import generate_synthetic_data
from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RetrainEngine:
    """
    Automated Model Retraining Engine.

    Features:
    - Triggered retraining based on drift/accuracy thresholds
    - Sandboxed training environment
    - Automated validation
    - Explainability checks (mock SHAP)
    - Fairness checks (synthetic metrics)
    - Performance comparison
    - Automatic promotion if improved
    """

    def __init__(self):
        self.model_registry = ModelRegistry()
        self.validator = ModelValidator()

        # Training configuration
        self.config = {
            "min_training_samples": 100,
            "validation_split": 0.2,
            "random_state": 42,
            "n_estimators": 100,
            "max_depth": 10,
        }

        # Performance thresholds
        self.thresholds = {
            "min_accuracy": 0.70,
            "min_precision": 0.65,
            "min_recall": 0.65,
            "improvement_margin": 0.02,  # Must be 2% better to promote
        }

        # Retraining history
        self.retrain_history: list[Dict[str, Any]] = []

    def train_initial_model(self) -> str:
        """
        Train initial model with synthetic data.

        Returns:
        --------
        str
            Version ID of trained model
        """
        logger.info("🔄 Training initial model...")

        # Generate synthetic training data
        X, y = generate_synthetic_data(n_samples=1000, n_features=3, random_state=42)

        # Train model
        version = self._train_and_register(
            X, y, reason="initial_training", drift_score=0.0
        )

        # Set as champion
        self.model_registry.set_champion(version)

        logger.info(f"✅ Initial model trained: version={version}")

        return version

    def trigger_retraining(
        self,
        drift_score: float,
        current_accuracy: Optional[float] = None,
        reason: str = "drift_detected",
    ) -> Dict[str, Any]:
        """
        Trigger automated retraining pipeline.

        Parameters:
        -----------
        drift_score : float
            Current drift score (0-100)
        current_accuracy : float, optional
            Current model accuracy
        reason : str
            Reason for retraining

        Returns:
        --------
        Dict
            Retraining results including success status and new version
        """
        logger.info(
            f"🚀 Retraining triggered: reason={reason}, drift_score={drift_score:.2f}"
        )

        start_time = datetime.now(timezone.utc)

        # Step 1: Generate training data (in production, extract from data stream)
        logger.info("📊 Extracting training window...")
        X_train, y_train = generate_synthetic_data(
            n_samples=500,
            n_features=3,
            drift_amount=drift_score / 100.0,  # Introduce drift proportional to score
        )

        if len(X_train) < self.config["min_training_samples"]:
            logger.warning(
                f"Insufficient training data: {len(X_train)} < {self.config['min_training_samples']}"
            )
            return {
                "success": False,
                "reason": "insufficient_data",
                "samples": len(X_train),
            }

        # Step 2: Train new model
        logger.info("🤖 Training new model...")
        new_version = self._train_and_register(
            X_train, y_train, reason=reason, drift_score=drift_score
        )

        # Step 3: Load new and current models
        new_model = self.model_registry.load_model(new_version)
        current_metadata = self.model_registry.get_champion_model()

        if current_metadata is None:
            # No current model, auto-promote
            self.model_registry.set_champion(new_version)
            logger.info(
                f"✅ New model auto-promoted (no previous champion): {new_version}"
            )
            return {
                "success": True,
                "version": new_version,
                "promoted": True,
                "reason": "no_previous_champion",
            }

        # Step 4: Validate new model
        logger.info("✔️ Validating new model...")
        X_val, y_val = generate_synthetic_data(n_samples=200, n_features=3)

        validation_result = self.validator.validate_model(
            model=new_model,
            X_val=X_val,
            y_val=y_val,
            feature_names=["feature_0", "feature_1", "feature_2"],
        )

        if not validation_result["passed"]:
            logger.warning(
                f"❌ New model failed validation: {validation_result['failures']}"
            )
            return {
                "success": False,
                "version": new_version,
                "promoted": False,
                "reason": "validation_failed",
                "validation": validation_result,
            }

        # Step 5: Compare performance
        logger.info("📊 Comparing performance with current champion...")

        new_metadata = self.model_registry.get_model_metadata(new_version)
        new_accuracy = new_metadata.accuracy
        current_accuracy_actual = current_metadata.accuracy

        improvement = new_accuracy - current_accuracy_actual

        # Step 6: Decide on promotion
        promoted = False
        if improvement >= self.thresholds["improvement_margin"]:
            logger.info(f"✅ New model is better by {improvement:.4f}, promoting...")
            self.model_registry.set_champion(new_version)
            promoted = True
        else:
            logger.info(
                f"⚠️ New model not significantly better (improvement: {improvement:.4f}), keeping current champion"
            )

        # Step 7: Log retraining event
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        retrain_event = {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "reason": reason,
            "drift_score": drift_score,
            "old_version": current_metadata.version,
            "new_version": new_version,
            "old_accuracy": current_accuracy_actual,
            "new_accuracy": new_accuracy,
            "improvement": improvement,
            "promoted": promoted,
            "validation": validation_result,
        }

        self.retrain_history.append(retrain_event)
        self._save_retrain_log(retrain_event)

        logger.info(
            f"✅ Retraining completed: version={new_version}, promoted={promoted}"
        )

        # Assuming 'success' is implicitly True if we reach this point without returning earlier
        # and 'version' refers to 'new_version', 'accuracy' refers to 'new_accuracy'
        # The original return had 'success': True, 'version': new_version, 'promoted': promoted,
        # 'old_accuracy': current_accuracy_actual, 'new_accuracy': new_accuracy,
        # 'improvement': improvement, 'validation': validation_result, 'duration_seconds': duration
        # The requested change seems to be a different set of keys and conversions.
        # I will replace the existing return dictionary with the new one,
        # interpreting 'success' as 'promoted' for the message, and using 'new_version' and 'new_accuracy'.
        # interpreting 'success' as 'promoted' for the message, and using 'new_version' and 'new_accuracy'.
        result = {
            "success": bool(
                promoted
            ),  # Using 'promoted' as the success indicator for the final outcome
            "version": str(new_version) if new_version else None,
            "promoted": bool(promoted),
            "drift_score": float(drift_score),
            "accuracy": float(new_accuracy) if new_accuracy is not None else None,
            "message": "Retraining triggered successfully"
            if promoted
            else "Retraining completed, but model not promoted",
            "improvement": improvement,
            "validation": validation_result,
            "duration_seconds": duration,
        }
        return convert_numpy_types(result)  # type: ignore

    def _train_and_register(
        self, X: np.ndarray, y: np.ndarray, reason: str, drift_score: float
    ) -> str:
        """Train model and register in registry"""

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X,
            y,
            test_size=self.config["validation_split"],
            random_state=self.config["random_state"],
        )

        # Train model
        model = RandomForestClassifier(
            n_estimators=self.config["n_estimators"],
            max_depth=self.config["max_depth"],
            random_state=self.config["random_state"],
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)

        # Create metadata
        version = f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        metadata = ModelMetadata(
            version=version,
            created_at=datetime.now(timezone.utc).isoformat(),
            model_type="RandomForestClassifier",
            accuracy=accuracy,
            drift_score=drift_score,
            training_samples=len(X_train),
            validation_samples=len(X_val),
            hyperparameters={
                "n_estimators": self.config["n_estimators"],
                "max_depth": self.config["max_depth"],
                "random_state": self.config["random_state"],
            },
            feature_names=[f"feature_{i}" for i in range(X.shape[1])],
            checksum="",  # Will be calculated by registry
            notes=f"Trained due to: {reason}",
        )

        # Register model
        self.model_registry.register_model(model, metadata)

        return version

    def _save_retrain_log(self, event: Dict[str, Any]):
        """Save retraining event to audit log"""
        log_dir = Path("logs/audit")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "retraining_events.jsonl"

        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def get_retrain_history(self, limit: int = 10) -> list:
        """Get recent retraining history"""
        return self.retrain_history[-limit:]
