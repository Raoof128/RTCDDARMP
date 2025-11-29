"""
Model Registry API Endpoint
"""

from fastapi import APIRouter, HTTPException, Request

from backend.utils.json_encoder import convert_numpy_types
from backend.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/model/latest")
async def get_latest_model(fastapi_request: Request):
    """
    Get latest model metadata.

    Returns:
    --------
    Dict
        Model metadata
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        metadata = model_registry.get_latest_model()

        if metadata is None:
            raise HTTPException(status_code=404, detail="No models found")

        from dataclasses import asdict

        return asdict(metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get latest model error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/champion")
async def get_champion_model(fastapi_request: Request):
    """
    Get current champion (deployed) model metadata.

    Returns:
    --------
    Dict
        Champion model metadata
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        metadata = model_registry.get_champion_model()

        if metadata is None:
            raise HTTPException(status_code=404, detail="No champion model found")

        from dataclasses import asdict

        return convert_numpy_types(asdict(metadata))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get champion model error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/list")
async def list_models(fastapi_request: Request):
    """
    List all registered models.

    Returns:
    --------
    Dict
        List of all model metadata
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        models = model_registry.list_models()

        from dataclasses import asdict

        return convert_numpy_types({"models": models, "count": len(models)})

    except Exception as e:
        logger.error(f"List models error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{version}")
async def get_model_metadata(version: str, fastapi_request: Request):
    """
    Get model metadata by version.

    Parameters:
    -----------
    version : str
        Model version

    Returns:
    --------
    Dict
        Model metadata
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        metadata = model_registry.get_model_metadata(version)

        if metadata is None:
            raise HTTPException(
                status_code=404, detail=f"Model version {version} not found"
            )

        from dataclasses import asdict

        return convert_numpy_types(asdict(metadata))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get model by version error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/{version}/promote")
async def promote_model(version: str, fastapi_request: Request):
    """
    Promote a model version.

    Parameters:
    -----------
    version : str
        Model version to promote

    Returns:
    --------
    Dict
        Confirmation message
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        success = model_registry.promote_model(version)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Model version {version} not found"
            )

        return {"status": "success", "message": f"Model {version} promoted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Promote model error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/{version}/set_champion")
async def set_champion(version: str, fastapi_request: Request):
    """
    Set a model as champion (deployed).

    Parameters:
    -----------
    version : str
        Model version to set as champion

    Returns:
    --------
    Dict
        Confirmation message
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        success = model_registry.set_champion(version)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Model version {version} not found"
            )

        return {"status": "success", "message": f"Model {version} set as champion"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set champion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/{version}/rollback")
async def rollback_model(version: str, fastapi_request: Request):
    """
    Rollback to a previous model version.

    Parameters:
    -----------
    version : str
        Model version to rollback to

    Returns:
    --------
    Dict
        Confirmation message
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        success = model_registry.rollback_to_version(version)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Cannot rollback to version {version}"
            )

        return {
            "status": "success",
            "message": f"Rolled back to model {version}",
            "warning": "This is a critical operation that was logged in audit trail",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/model/{version}")
async def delete_model(version: str, fastapi_request: Request):
    """
    Delete a model version (cannot delete champion).

    Parameters:
    -----------
    version : str
        Model version to delete

    Returns:
    --------
    Dict
        Confirmation message
    """
    try:
        model_registry = fastapi_request.app.state.model_registry
        success = model_registry.delete_model(version)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete model {version} (not found or is champion)",
            )

        return {"status": "success", "message": f"Model {version} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete model error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
