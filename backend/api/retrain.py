"""
Retraining API Endpoint
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.engines.retrain_engine import RetrainEngine
from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class RetrainRequest(BaseModel):
    """Retrain request schema"""

    drift_score: float = Field(..., description="Current drift score (0-100)")
    current_accuracy: Optional[float] = Field(
        None, description="Current model accuracy"
    )
    reason: str = Field(default="manual_trigger", description="Reason for retraining")


@router.post("/force_retrain")
async def force_retrain(request: RetrainRequest):
    """
    Manually trigger model retraining.

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
    try:
        engine = RetrainEngine()

        logger.info(
            f"Manual retraining triggered: reason={request.reason}, drift_score={request.drift_score}"
        )

        result = engine.trigger_retraining(
            drift_score=request.drift_score,
            current_accuracy=request.current_accuracy,
            reason=request.reason,
        )

        return convert_numpy_types(result)

    except Exception as e:
        logger.error(f"Retraining error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto_retrain_check")
async def auto_retrain_check(
    drift_score: float, current_accuracy: Optional[float] = None
):
    """
    Check if auto-retraining should be triggered based on thresholds.

    Parameters:
    -----------
    drift_score : float
        Current drift score (0-100)
    current_accuracy : float, optional
        Current model accuracy

    Returns:
    --------
    Dict
        Decision and recommendation
    """
    try:
        # Thresholds
        DRIFT_THRESHOLD = 70.0
        ACCURACY_THRESHOLD = 0.85

        should_retrain = False
        reason = ""

        if drift_score >= DRIFT_THRESHOLD:
            should_retrain = True
            reason = f"drift_threshold_exceeded (score: {drift_score:.2f} >= {DRIFT_THRESHOLD})"

        if current_accuracy is not None and current_accuracy < ACCURACY_THRESHOLD:
            should_retrain = True
            if reason:
                reason += " AND "
            reason += f"accuracy_below_threshold ({current_accuracy:.4f} < {ACCURACY_THRESHOLD})"

        if should_retrain:
            # Trigger retraining
            engine = RetrainEngine()
            result = engine.trigger_retraining(
                drift_score=drift_score,
                current_accuracy=current_accuracy,
                reason=f"auto_triggered: {reason}",
            )

            return {
                "should_retrain": True,
                "reason": reason,
                "retraining_result": result,
            }
        else:
            return {
                "should_retrain": False,
                "reason": "No thresholds exceeded",
                "drift_score": drift_score,
                "current_accuracy": current_accuracy,
            }

    except Exception as e:
        logger.error(f"Auto-retrain check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retrain/history")
async def get_retrain_history(limit: int = 10):
    """
    Get retraining history.

    Parameters:
    -----------
    limit : int
        Number of recent entries to return

    Returns:
    --------
    Dict
        Retraining history
    """
    try:
        engine = RetrainEngine()
        history = engine.get_retrain_history(limit=limit)

        return {"history": history, "count": len(history)}

    except Exception as e:
        logger.error(f"Get retrain history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
