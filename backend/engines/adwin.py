"""
ADWIN (Adaptive Windowing) Drift Detector
Implementation of the ADWIN algorithm for detecting concept drift in data streams.

Reference: Bifet, A., & Gavaldà, R. (2007). Learning from time-changing data with adaptive windowing.
"""

from collections import deque

import numpy as np


class ADWIN:
    """
    Adaptive Windowing (ADWIN) drift detector.

    ADWIN maintains a variable-length window of recently seen data and automatically
    detects when the data distribution changes significantly.

    Parameters:
    -----------
    delta : float, default=0.002
        Confidence parameter. The smaller delta, the more confident we need to be
        that there is a change before flagging drift. Typical values: 0.002 to 0.1
    """

    def __init__(self, delta: float = 0.002):
        self.delta = delta
        self.window = deque()
        self.total = 0.0
        self.variance = 0.0
        self.width = 0
        self.drift_detected = False
        self.drift_count = 0

    def add_element(self, value: float) -> bool:
        """
        Add a new element to the window and check for drift.

        Parameters:
        -----------
        value : float
            The new value to add (typically 0 for correct, 1 for error)

        Returns:
        --------
        bool
            True if drift was detected, False otherwise
        """
        self.window.append(value)
        self.width += 1

        # Update statistics
        if self.width == 1:
            self.total = value
            self.variance = 0.0
        else:
            old_mean = self.total / (self.width - 1)
            self.total += value
            new_mean = self.total / self.width
            self.variance += (value - old_mean) * (value - new_mean)

        # Check for drift
        self.drift_detected = False

        if self.width > 1:
            drift_detected = self._detect_change()
            if drift_detected:
                self.drift_detected = True
                self.drift_count += 1
                return True

        return False

    def _detect_change(self) -> bool:
        """
        Check if there's a significant change between two subwindows.

        Returns:
        --------
        bool
            True if change detected, False otherwise
        """
        # Convert deque to list for easier manipulation
        window_list = list(self.window)
        n = len(window_list)

        # Try different split points
        for i in range(1, n):
            # Split window into two parts
            w0 = window_list[:i]
            w1 = window_list[i:]

            n0 = len(w0)
            n1 = len(w1)

            if n0 < 5 or n1 < 5:  # Need minimum samples
                continue

            # Calculate means
            mean0 = np.mean(w0)
            mean1 = np.mean(w1)



            # Hoeffding bound
            m = 1.0 / (1.0 / n0 + 1.0 / n1)
            epsilon = np.sqrt((1.0 / (2 * m)) * np.log(4.0 / self.delta))

            # Check if difference is significant
            if abs(mean0 - mean1) > epsilon:
                # Remove older elements
                for _ in range(i):
                    removed = self.window.popleft()
                    self.total -= removed
                    self.width -= 1

                # Recalculate variance
                if self.width > 0:
                    remaining = list(self.window)
                    self.variance = (
                        np.var(remaining) * self.width if self.width > 1 else 0
                    )

                return True

        return False

    def reset(self):
        """Reset the detector to initial state"""
        self.window.clear()
        self.total = 0.0
        self.variance = 0.0
        self.width = 0
        self.drift_detected = False

    def get_width(self) -> int:
        """Get current window width"""
        return self.width

    def get_mean(self) -> float:
        """Get mean of current window"""
        return self.total / self.width if self.width > 0 else 0.0

    def get_variance(self) -> float:
        """Get variance of current window"""
        if self.width < 2:
            return 0.0
        return self.variance / (self.width - 1)

    def get_drift_count(self) -> int:
        """Get total number of drifts detected"""
        return self.drift_count
