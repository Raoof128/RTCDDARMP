"""
Drift Detection API Endpoint
"""

from typing import List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.engines.drift_detector import DriftDetector
from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Global drift detector instance
drift_detector: Optional[DriftDetector] = None


def get_drift_detector(n_features: int = 3) -> DriftDetector:
    """Get or create drift detector instance"""
    global drift_detector
    if drift_detector is None:
        drift_detector = DriftDetector(n_features=n_features)
        logger.info("Drift detector initialized")
    return drift_detector


class IngestRequest(BaseModel):
    """Data ingestion request schema"""

    features: List[float] = Field(..., description="Feature vector")
    label: Optional[float] = Field(None, description="True label (optional)")
    prediction: Optional[float] = Field(None, description="Model prediction (optional)")


@router.post("/ingest")
async def ingest_data(request: IngestRequest):
    """
    Ingest streaming data for drift monitoring.

    Parameters:
    -----------
    features : List[float]
        Feature vector
    label : float, optional
        True label
    prediction : float, optional
        Model prediction

    Returns:
    --------
    Dict
        Ingestion confirmation
    """
    try:
        detector = get_drift_detector(n_features=len(request.features))

        # Convert to numpy
        features_array = np.array(request.features)

        # Calculate error if both label and prediction provided
        error = 0.0
        if request.label is not None and request.prediction is not None:
            error = 1.0 if request.label != request.prediction else 0.0

        # Add sample to drift detector
        detector.add_sample(
            features=features_array,
            label=request.label,
            prediction=request.prediction,
            error=error,
        )

        return {
            "status": "success",
            "message": "Data ingested successfully",
            "current_window_size": len(detector.current_features),
        }

    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_reference")
async def set_reference_data(
    features: List[List[float]],
    labels: Optional[List[float]] = None,
    predictions: Optional[List[float]] = None,
):
    """
    Set reference (baseline) distribution for drift detection.

    Parameters:
    -----------
    features : List[List[float]]
        Reference feature matrix
    labels : List[float], optional
        Reference labels
    predictions : List[float], optional
        Reference predictions

    Returns:
    --------
    Dict
        Confirmation message
    """
    try:
        detector = get_drift_detector(n_features=len(features[0]))

        # Convert to numpy
        features_array = np.array(features)
        labels_array = np.array(labels) if labels else None
        predictions_array = np.array(predictions) if predictions else None

        detector.set_reference(
            features=features_array, labels=labels_array, predictions=predictions_array
        )

        return {
            "status": "success",
            "message": "Reference distribution set",
            "n_samples": len(features_array),
        }

    except Exception as e:
        logger.error(f"Set reference error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift")
async def get_drift_status():
    """Get current drift detection results."""
    try:
        # Ensure drift_detector is initialized
        detector = get_drift_detector()
        result = detector.detect_drift()
        return convert_numpy_types(result)
    except Exception as e:
        logger.error(f"Error getting drift status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/history")
async def get_drift_history(limit: int = 10):
    """
    Get drift detection history.

    Parameters:
    -----------
    limit : int
        Number of recent entries to return

    Returns:
    --------
    List[Dict]
        Drift history
    """
    try:
        detector = get_drift_detector()
        history = detector.get_drift_history(limit=limit)

        return {"history": history, "count": len(history)}

    except Exception as e:
        logger.error(f"Get history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drift/reset")
async def reset_drift_detector():
    """
    Reset drift detector state.

    Returns:
    --------
    Dict
        Confirmation message
    """
    try:
        detector = get_drift_detector()
        detector.reset()

        logger.info("Drift detector reset")

        return {"status": "success", "message": "Drift detector reset"}

    except Exception as e:
        logger.error(f"Reset error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
