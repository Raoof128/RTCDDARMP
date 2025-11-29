"""
RCD² - Real-Time Concept Drift Detector & Auto-Retraining ML Pipeline
FastAPI Backend Main Application
"""

import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Import Routers
from backend.api import dashboard, drift, metrics, model, predict, retrain
from backend.engines.model_registry import ModelRegistry
from backend.utils.logger import get_logger
from backend.utils.security import get_api_key

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 RCD² Platform Starting Up...")

    # Security Check
    if not os.getenv("RCD2_API_KEY"):
        generated_key = secrets.token_urlsafe(32)
        os.environ["RCD2_API_KEY"] = generated_key
        logger.warning(
            f"⚠️  RCD2_API_KEY not set. Generated temporary key: {generated_key}"
        )
        logger.warning(
            "👉 Please set RCD2_API_KEY in your environment for production use."
        )

    # Initialize directories
    dirs = ["models", "logs", "data", "logs/audit"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Initialize model registry
    app.state.model_registry = ModelRegistry()
    logger.info("✅ Model Registry Initialized")

    # Train initial model if none exists
    from backend.engines.retrain_engine import RetrainEngine

    retrain_engine = RetrainEngine()
    if not app.state.model_registry.get_latest_model():
        logger.info("📦 Training initial model...")
        retrain_engine.train_initial_model()
        logger.info("✅ Initial model trained successfully")

    logger.info("✅ RCD² Platform Ready!")

    yield

    # Shutdown
    logger.info("🛑 RCD² Platform Shutting Down...")


app = FastAPI(
    title="RCD² Platform",
    description="Real-Time Concept Drift Detector & Auto-Retraining Pipeline",
    version="1.0.0",
    lifespan=lifespan,
    # Enforce security globally, but allow overriding for specific public endpoints if needed
    # dependencies=[Depends(get_api_key)]
)

# We apply security to specific routers to allow public access to dashboard/health if desired.
# For High Security Mode, we will secure API endpoints but leave Dashboard UI accessible
# (Dashboard JS will need the key to fetch data).

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with Security
app.include_router(
    predict.router,
    prefix="/api",
    tags=["Prediction"],
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    drift.router,
    prefix="/api",
    tags=["Drift Detection"],
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    retrain.router,
    prefix="/api",
    tags=["Retraining"],
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    model.router,
    prefix="/api",
    tags=["Model Registry"],
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    metrics.router, prefix="/api", tags=["Metrics"], dependencies=[Depends(get_api_key)]
)

# Dashboard & Health (Public Access)
app.include_router(dashboard.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to dashboard"""
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/dashboard" />
        <title>RCD² Platform</title>
    </head>
    <body>
        <p>Redirecting to <a href="/dashboard">dashboard</a>...</p>
    </body>
    </html>
    """
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure all errors return JSON.
    Prevents raw 500 HTML pages and leaks of stack traces in production.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc)
            if os.getenv("ENVIRONMENT") == "development"
            else "An unexpected error occurred.",
        },
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RCD² Platform", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
