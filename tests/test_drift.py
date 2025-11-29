"""
Tests for drift detection engines
"""

import numpy as np
import pytest

from backend.engines.adwin import ADWIN
from backend.engines.drift_detector import DriftDetector
from backend.engines.stat_tests import (
    kl_divergence,
    kolmogorov_smirnov_test,
    population_stability_index,
)


class TestADWIN:
    """Test ADWIN drift detector"""

    def test_initialization(self):
        """Test ADWIN initialization"""
        adwin = ADWIN(delta=0.002)
        assert adwin.width == 0
        assert adwin.drift_detected is False

    def test_add_element(self):
        """Test adding elements"""
        adwin = ADWIN()
        adwin.add_element(0.5)
        assert adwin.width == 1
        assert adwin.get_mean() == 0.5

    def test_drift_detection(self):
        """Test drift detection with clear distribution change"""
        adwin = ADWIN(delta=0.01)

        # Add stable data
        for _ in range(50):
            adwin.add_element(0.0)

        # Add drifted data
        drift_detected = False
        for _ in range(50):
            if adwin.add_element(1.0):
                drift_detected = True
                break

        assert drift_detected or adwin.width < 100  # Either detected or shrunk window


class TestStatisticalTests:
    """Test statistical drift tests"""

    def test_ks_test_same_distribution(self):
        """Test KS test with same distribution"""
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        curr = np.random.normal(0, 1, 1000)

        statistic, p_value, drift = kolmogorov_smirnov_test(ref, curr)

        assert statistic >= 0
        assert 0 <= p_value <= 1
        # Should not detect drift (high p-value)
        assert drift is False or p_value > 0.01

    def test_ks_test_different_distribution(self):
        """Test KS test with different distributions"""
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        curr = np.random.normal(2, 1, 1000)  # Different mean

        statistic, p_value, drift = kolmogorov_smirnov_test(ref, curr)

        assert drift  # Should detect drift
        assert p_value < 0.05

    def test_psi_no_drift(self):
        """Test PSI with no drift"""
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        curr = np.random.normal(0, 1, 1000)

        psi = population_stability_index(ref, curr)

        assert psi < 0.1  # No significant drift

    def test_psi_with_drift(self):
        """Test PSI with drift"""
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        curr = np.random.normal(2, 1, 1000)

        psi = population_stability_index(ref, curr)

        assert psi > 0.2  # Significant drift

    def test_kl_divergence(self):
        """Test KL divergence"""
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        curr = np.random.normal(0, 1, 1000)

        kl = kl_divergence(ref, curr)

        assert kl >= 0  # KL divergence is non-negative


class TestDriftDetector:
    """Test main drift detector"""

    def test_initialization(self):
        """Test detector initialization"""
        detector = DriftDetector(n_features=3)
        assert detector.n_features == 3
        assert len(detector.adwin_detectors) == 4  # 3 features + 1 for predictions

    def test_set_reference(self):
        """Test setting reference distribution"""
        detector = DriftDetector(n_features=3)

        X_ref = np.random.randn(100, 3)
        y_ref = np.random.randint(0, 2, 100)

        detector.set_reference(X_ref, y_ref)

        assert detector.reference_features is not None
        assert detector.reference_labels is not None

    def test_add_sample(self):
        """Test adding samples"""
        detector = DriftDetector(n_features=3)

        features = np.array([0.5, 0.3, 0.8])
        detector.add_sample(features, label=1.0)

        assert len(detector.current_features) == 1
        assert len(detector.current_labels) == 1

    def test_detect_drift_no_reference(self):
        """Test drift detection without reference"""
        detector = DriftDetector(n_features=3)

        result = detector.detect_drift()

        assert result["drift_score"] == 0
        assert "error" in result["details"]

    def test_detect_drift_with_data(self):
        """Test drift detection with data"""
        np.random.seed(42)
        detector = DriftDetector(n_features=3)

        # Set reference
        X_ref = np.random.randn(100, 3)
        detector.set_reference(X_ref)

        # Add current samples (no drift)
        for i in range(50):
            features = np.random.randn(3)
            detector.add_sample(features)

        result = detector.detect_drift()

        assert "drift_score" in result
        assert "severity" in result
        assert "drift_type" in result

    def test_reset(self):
        """Test detector reset"""
        detector = DriftDetector(n_features=3)

        # Add samples
        for i in range(10):
            detector.add_sample(np.random.randn(3))

        detector.reset()

        assert len(detector.current_features) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
