"""
Statistical Tests for Drift Detection
Includes KS Test, PSI, KL Divergence, and other statistical measures
"""

from typing import Tuple

import numpy as np
from scipy import stats


def kolmogorov_smirnov_test(
    reference: np.ndarray, current: np.ndarray, alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Kolmogorov-Smirnov test for distribution comparison.

    Parameters:
    -----------
    reference : np.ndarray
        Reference (baseline) distribution
    current : np.ndarray
        Current distribution to compare
    alpha : float
        Significance level (default: 0.05)

    Returns:
    --------
    Tuple[float, float, bool]
        (statistic, p_value, drift_detected)
    """
    statistic, p_value = stats.ks_2samp(reference, current)
    drift_detected = p_value < alpha

    return statistic, p_value, drift_detected


def population_stability_index(
    reference: np.ndarray, current: np.ndarray, bins: int = 10
) -> float:
    """
    Calculate Population Stability Index (PSI).

    PSI measures the shift in a variable's distribution between two samples.

    PSI Interpretation:
    - PSI < 0.1: No significant change
    - 0.1 <= PSI < 0.2: Moderate change
    - PSI >= 0.2: Significant change (drift detected)

    Parameters:
    -----------
    reference : np.ndarray
        Reference (baseline) distribution
    current : np.ndarray
        Current distribution to compare
    bins : int
        Number of bins for discretization

    Returns:
    --------
    float
        PSI value
    """
    # Define bin edges based on reference distribution
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bin_edges = np.linspace(min_val, max_val, bins + 1)

    # Calculate frequencies
    ref_freq, _ = np.histogram(reference, bins=bin_edges)
    curr_freq, _ = np.histogram(current, bins=bin_edges)

    # Convert to proportions
    ref_prop = ref_freq / len(reference)
    curr_prop = curr_freq / len(current)

    # Avoid division by zero and log(0)
    ref_prop = np.where(ref_prop == 0, 0.0001, ref_prop)
    curr_prop = np.where(curr_prop == 0, 0.0001, curr_prop)

    # Calculate PSI
    psi = np.sum((curr_prop - ref_prop) * np.log(curr_prop / ref_prop))

    return psi


def kl_divergence(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Kullback-Leibler Divergence.

    KL divergence measures how one probability distribution diverges from
    a reference distribution.

    Parameters:
    -----------
    reference : np.ndarray
        Reference (baseline) distribution
    current : np.ndarray
        Current distribution to compare
    bins : int
        Number of bins for discretization

    Returns:
    --------
    float
        KL divergence value
    """
    # Define bin edges
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bin_edges = np.linspace(min_val, max_val, bins + 1)

    # Calculate frequencies
    ref_freq, _ = np.histogram(reference, bins=bin_edges)
    curr_freq, _ = np.histogram(current, bins=bin_edges)

    # Convert to probabilities
    ref_prob = ref_freq / len(reference)
    curr_prob = curr_freq / len(current)

    # Avoid log(0)
    ref_prob = np.where(ref_prob == 0, 1e-10, ref_prob)
    curr_prob = np.where(curr_prob == 0, 1e-10, curr_prob)

    # Calculate KL divergence
    kl_div = np.sum(curr_prob * np.log(curr_prob / ref_prob))

    return kl_div


def jensen_shannon_divergence(
    reference: np.ndarray, current: np.ndarray, bins: int = 10
) -> float:
    """
    Calculate Jensen-Shannon Divergence (symmetric version of KL).

    Parameters:
    -----------
    reference : np.ndarray
        Reference distribution
    current : np.ndarray
        Current distribution
    bins : int
        Number of bins

    Returns:
    --------
    float
        JS divergence value (0 to 1)
    """
    # Define bin edges
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bin_edges = np.linspace(min_val, max_val, bins + 1)

    # Calculate probabilities
    ref_freq, _ = np.histogram(reference, bins=bin_edges)
    curr_freq, _ = np.histogram(current, bins=bin_edges)

    ref_prob = ref_freq / len(reference)
    curr_prob = curr_freq / len(current)

    # Avoid log(0)
    ref_prob = np.where(ref_prob == 0, 1e-10, ref_prob)
    curr_prob = np.where(curr_prob == 0, 1e-10, curr_prob)

    # Calculate middle distribution
    m = 0.5 * (ref_prob + curr_prob)

    # Calculate JS divergence
    js_div = 0.5 * np.sum(ref_prob * np.log(ref_prob / m)) + 0.5 * np.sum(
        curr_prob * np.log(curr_prob / m)
    )

    return js_div


def wasserstein_distance(reference: np.ndarray, current: np.ndarray) -> float:
    """
    Calculate Wasserstein distance (Earth Mover's Distance).

    Parameters:
    -----------
    reference : np.ndarray
        Reference distribution
    current : np.ndarray
        Current distribution

    Returns:
    --------
    float
        Wasserstein distance
    """
    return stats.wasserstein_distance(reference, current)


def chi_square_test(
    reference: np.ndarray, current: np.ndarray, bins: int = 10, alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Chi-square test for distribution comparison.

    Parameters:
    -----------
    reference : np.ndarray
        Reference distribution
    current : np.ndarray
        Current distribution
    bins : int
        Number of bins
    alpha : float
        Significance level

    Returns:
    --------
    Tuple[float, float, bool]
        (statistic, p_value, drift_detected)
    """
    # Define bin edges
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bin_edges = np.linspace(min_val, max_val, bins + 1)

    # Calculate observed frequencies
    ref_freq, _ = np.histogram(reference, bins=bin_edges)
    curr_freq, _ = np.histogram(current, bins=bin_edges)

    # Avoid zero frequencies
    ref_freq = np.where(ref_freq == 0, 1, ref_freq)

    # Chi-square test
    statistic, p_value = stats.chisquare(curr_freq, ref_freq)
    drift_detected = p_value < alpha

    return statistic, p_value, drift_detected
