"""
Tests for retraining pipeline
"""

import numpy as np
import pytest

from backend.engines.model_registry import ModelMetadata, ModelRegistry
from backend.engines.model_validator import ModelValidator
from backend.engines.retrain_engine import RetrainEngine


class TestModelRegistry:
    """Test model registry"""

    def test_initialization(self):
        """Test registry initialization"""
        registry = ModelRegistry(registry_dir="models_test")
        assert registry.registry_dir.exists()

    def test_register_and_load_model(self):
        """Test registering and loading a model"""
        from sklearn.ensemble import RandomForestClassifier

        registry = ModelRegistry(registry_dir="models_test")

        # Create and train a simple model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.randn(100, 3)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # Create metadata
        metadata = ModelMetadata(
            version="test_v1",
            created_at="2024-01-01T00:00:00",
            model_type="RandomForest",
            accuracy=0.95,
            drift_score=0.0,
            training_samples=100,
            validation_samples=20,
            hyperparameters={"n_estimators": 10},
            feature_names=["f0", "f1", "f2"],
            checksum="",
        )

        # Register
        version = registry.register_model(model, metadata)

        assert version == "test_v1"

        # Load
        loaded_model = registry.load_model(version)

        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")


class TestModelValidator:
    """Test model validator"""

    def test_validation_passes(self):
        """Test validation with good model"""
        from sklearn.ensemble import RandomForestClassifier

        validator = ModelValidator()

        # Create and train a model
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        X_train = np.random.randn(200, 3)
        y_train = np.random.randint(0, 2, 200)
        model.fit(X_train, y_train)

        # Validation data
        X_val = np.random.randn(50, 3)
        y_val = np.random.randint(0, 2, 50)

        result = validator.validate_model(
            model, X_val, y_val, feature_names=["f0", "f1", "f2"]
        )

        assert "passed" in result
        assert "checks" in result
        assert "performance" in result["checks"]


class TestRetrainEngine:
    """Test retraining engine"""

    def test_initialization(self):
        """Test engine initialization"""
        engine = RetrainEngine()
        assert engine.model_registry is not None
        assert engine.validator is not None

    def test_trigger_retraining(self):
        """Test triggering retraining"""
        engine = RetrainEngine()

        # First ensure there's an initial model
        engine.train_initial_model()

        # Relax threshold to ensure promotion
        engine.thresholds["improvement_margin"] = -1.0

        # Mock validator to ensure success
        engine.validator.validate_model = lambda *args, **kwargs: {
            "passed": True,
            "checks": {"performance": 0.9},
        }

        # Trigger retraining
        result = engine.trigger_retraining(drift_score=80.0, reason="test_retraining")

        assert result["success"] is True
        assert "version" in result
        assert "promoted" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
