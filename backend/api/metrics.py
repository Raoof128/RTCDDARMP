"""
Metrics API Endpoint
"""

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_metrics(fastapi_request: Request):
    """
    Get comprehensive platform metrics.

    Returns:
    --------
    Dict
        Platform metrics including model performance, drift, and system health
    """
    try:
        model_registry = fastapi_request.app.state.model_registry

        # Get champion model metrics
        champion = model_registry.get_champion_model()

        if champion:
            from dataclasses import asdict

            champion_data = asdict(champion)
        else:
            champion_data = None

        # Get all models count
        all_models = model_registry.list_models()

        # Get drift detector status (if initialized)
        from backend.api.drift import drift_detector

        drift_status = None
        if drift_detector:
            drift_status = {
                "current_window_size": len(drift_detector.current_features),
                "max_window_size": drift_detector.window_size,
                "reference_set": drift_detector.reference_features is not None,
            }

        # Get retraining stats
        from backend.engines.retrain_engine import RetrainEngine

        retrain_engine = RetrainEngine()
        retrain_history = retrain_engine.get_retrain_history(limit=5)

        # Calculate retraining stats
        if retrain_history:
            total_retrains = len(retrain_history)
            successful_promotes = sum(
                1 for r in retrain_history if r.get("promoted", False)
            )
            avg_improvement = np.mean(
                [r.get("improvement", 0) for r in retrain_history]
            )
        else:
            total_retrains = 0
            successful_promotes = 0
            avg_improvement = 0.0

        metrics = {
            "champion_model": champion_data,
            "total_models": len(all_models),
            "drift_detector": drift_status,
            "retraining_stats": {
                "total_retrains": total_retrains,
                "successful_promotes": successful_promotes,
                "promotion_rate": successful_promotes / total_retrains
                if total_retrains > 0
                else 0,
                "avg_improvement": float(avg_improvement),
            },
            "system_health": "healthy",
        }

        return convert_numpy_types(metrics)

    except Exception as e:
        logger.error(f"Get metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/drift_timeline")
async def get_drift_timeline(limit: int = 50):
    """
    Get drift score timeline for visualization.

    Parameters:
    -----------
    limit : int
        Number of recent drift events

    Returns:
    --------
    Dict
        Timeline data
    """
    try:
        from backend.api.drift import drift_detector

        if drift_detector is None or not drift_detector.drift_history:
            return {"timeline": [], "count": 0}

        history = drift_detector.get_drift_history(limit=limit)

        timeline = [
            {
                "timestamp": h.get("timestamp"),
                "drift_score": h.get("drift_score"),
                "severity": h.get("severity"),
                "drift_type": h.get("drift_type"),
            }
            for h in history
        ]

        return {"timeline": timeline, "count": len(timeline)}

    except Exception as e:
        logger.error(f"Get drift timeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/model_timeline")
async def get_model_timeline(fastapi_request: Request):
    """
    Get model version timeline.

    Returns:
    --------
    Dict
        Model version history
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        models = model_registry.list_models()

        # Sort by created_at
        sorted_models = sorted(models, key=lambda m: m.created_at)

        timeline = [
            {
                "version": m.version,
                "created_at": m.created_at,
                "accuracy": m.accuracy,
                "drift_score": m.drift_score,
                "champion": m.champion,
                "promoted": m.promoted,
            }
            for m in sorted_models
        ]

        return {"timeline": timeline, "count": len(timeline)}

    except Exception as e:
        logger.error(f"Get model timeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
