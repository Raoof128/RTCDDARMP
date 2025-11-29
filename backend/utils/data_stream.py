"""
Data Stream Generator and Utilities
"""

from typing import Optional, Tuple

import numpy as np


def generate_synthetic_data(
    n_samples: int = 1000,
    n_features: int = 3,
    n_classes: int = 2,
    random_state: Optional[int] = None,
    drift_amount: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic classification dataset.

    Parameters:
    -----------
    n_samples : int
        Number of samples to generate
    n_features : int
        Number of features
    n_classes : int
        Number of classes
    random_state : int, optional
        Random seed
    drift_amount : float
        Amount of drift to introduce (0.0 = no drift, 1.0 = maximum drift)

    Returns:
    --------
    Tuple[np.ndarray, np.ndarray]
        (X, y) feature matrix and labels
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Base distribution
    if drift_amount == 0.0:
        # No drift: standard normal distribution
        X = np.random.randn(n_samples, n_features)
    else:
        # Introduce drift by shifting mean and scaling std
        X = np.random.randn(n_samples, n_features)

        # Shift mean proportional to drift
        shift = drift_amount * 2.0
        X += shift

        # Scale std proportional to drift
        scale = 1.0 + drift_amount * 0.5
        X *= scale

    # Generate labels using a simple linear decision boundary
    # with some noise
    weights = np.random.randn(n_features)
    decision_values = X.dot(weights)

    if n_classes == 2:
        # Binary classification
        y = (decision_values > 0).astype(int)

        # Add label noise (5%)
        noise_mask = np.random.rand(n_samples) < 0.05
        y[noise_mask] = 1 - y[noise_mask]
    else:
        # Multiclass
        # Divide decision values into n_classes bins
        percentiles = np.linspace(0, 100, n_classes + 1)
        thresholds = np.percentile(decision_values, percentiles[1:-1])

        y = np.zeros(n_samples, dtype=int)
        for i, threshold in enumerate(thresholds):
            y[decision_values > threshold] = i + 1

    return X, y


def add_gradual_drift(
    X: np.ndarray, start_idx: int, end_idx: int, drift_magnitude: float = 1.0
) -> np.ndarray:
    """
    Add gradual drift to data stream.

    Parameters:
    -----------
    X : np.ndarray
        Original data
    start_idx : int
        Index where drift starts
    end_idx : int
        Index where drift stabilizes
    drift_magnitude : float
        Magnitude of drift

    Returns:
    --------
    np.ndarray
        Data with gradual drift
    """
    X_drifted = X.copy()

    drift_length = end_idx - start_idx
    if drift_length <= 0:
        return X_drifted

    for i in range(start_idx, end_idx):
        # Linear interpolation of drift
        drift_progress = (i - start_idx) / drift_length
        shift = drift_progress * drift_magnitude

        X_drifted[i] += shift

    # Full drift after end_idx
    X_drifted[end_idx:] += drift_magnitude

    return X_drifted


def add_sudden_drift(
    X: np.ndarray, drift_idx: int, drift_magnitude: float = 1.0
) -> np.ndarray:
    """
    Add sudden (abrupt) drift to data stream.

    Parameters:
    -----------
    X : np.ndarray
        Original data
    drift_idx : int
        Index where drift occurs
    drift_magnitude : float
        Magnitude of drift

    Returns:
    --------
    np.ndarray
        Data with sudden drift
    """
    X_drifted = X.copy()
    X_drifted[drift_idx:] += drift_magnitude

    return X_drifted


def inject_noise(X: np.ndarray, noise_level: float = 0.1) -> np.ndarray:
    """
    Inject gaussian noise into data.

    Parameters:
    -----------
    X : np.ndarray
        Original data
    noise_level : float
        Noise standard deviation

    Returns:
    --------
    np.ndarray
        Noisy data
    """
    noise = np.random.randn(*X.shape) * noise_level
    return X + noise  # type: ignore


class DataStreamSimulator:
    """
    Simulates a data stream with configurable drift patterns.
    """

    def __init__(
        self,
        n_features: int = 3,
        n_classes: int = 2,
        base_samples: int = 1000,
        random_state: Optional[int] = None,
    ):
        self.n_features = n_features
        self.n_classes = n_classes
        self.base_samples = base_samples
        self.random_state = random_state

        # Generate base dataset
        self.X_base, self.y_base = generate_synthetic_data(
            n_samples=base_samples,
            n_features=n_features,
            n_classes=n_classes,
            random_state=random_state,
        )

        self.current_idx = 0

    def get_batch(
        self, batch_size: int = 10, drift_amount: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray, bool]:
        """
        Get next batch from stream.

        Parameters:
        -----------
        batch_size : int
            Size of batch
        drift_amount : float
            Amount of drift to apply

        Returns:
        --------
        Tuple[np.ndarray, np.ndarray, bool]
            (X_batch, y_batch, stream_ended)
        """
        if self.current_idx >= self.base_samples:
            # Stream ended, reset
            self.current_idx = 0
            return np.array([]), np.array([]), True

        end_idx = min(self.current_idx + batch_size, self.base_samples)

        X_batch = self.X_base[self.current_idx : end_idx].copy()
        y_batch = self.y_base[self.current_idx : end_idx].copy()

        # Apply drift if specified
        if drift_amount > 0:
            X_batch += np.random.randn(*X_batch.shape) * drift_amount

        self.current_idx = end_idx

        return X_batch, y_batch, False

    def reset(self):
        """Reset stream to beginning"""
        self.current_idx = 0
