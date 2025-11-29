"""
Prediction API Endpoint
"""

from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class PredictionRequest(BaseModel):
    """Prediction request schema"""

    features: List[float] = Field(..., description="Feature vector for prediction")


class PredictionResponse(BaseModel):
    """Prediction response schema"""

    prediction: int
    probability: List[float]
    model_version: str
    timestamp: str

    model_config = {"protected_namespaces": ()}


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, fastapi_request: Request):
    """
    Make prediction with current champion model.

    Parameters:
    -----------
    features : List[float]
        Feature vector

    Returns:
    --------
    PredictionResponse
        Prediction result with model version
    """
    try:
        # Get model registry from app state
        model_registry = fastapi_request.app.state.model_registry

        # Load champion model
        champion_metadata = model_registry.get_champion_model()

        if champion_metadata is None:
            raise HTTPException(status_code=503, detail="No model available")

        model = model_registry.load_model(champion_metadata.version)

        if model is None:
            raise HTTPException(status_code=503, detail="Failed to load model")

        # Prepare features
        X = np.array(request.features).reshape(1, -1)

        # Make prediction
        prediction = int(model.predict(X)[0])

        # Get probability if available
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0].tolist()
        else:
            proba = [1.0 if i == prediction else 0.0 for i in range(2)]

        from datetime import datetime, timezone

        response = PredictionResponse(
            prediction=prediction,
            probability=proba,
            model_version=champion_metadata.version,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Prediction made: {prediction} with model {champion_metadata.version}"
        )

        return response

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
async def predict_batch(features_list: List[List[float]], fastapi_request: Request):
    """
    Make batch predictions.

    Parameters:
    -----------
    features_list : List[List[float]]
        List of feature vectors

    Returns:
    --------
    Dict
        Batch prediction results
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        champion_metadata = model_registry.get_champion_model()

        if champion_metadata is None:
            raise HTTPException(status_code=503, detail="No model available")

        model = model_registry.load_model(champion_metadata.version)

        X = np.array(features_list)
        predictions = model.predict(X).tolist()

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X).tolist()
        else:
            probabilities = None

        from datetime import datetime, timezone

        return convert_numpy_types(
            {
                "predictions": predictions,
                "probabilities": probabilities,
                "model_version": champion_metadata.version,
                "count": len(predictions),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
