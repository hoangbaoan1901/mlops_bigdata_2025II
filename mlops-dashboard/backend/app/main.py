from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import mlflow_routes, kubeflow_routes, kserve_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MLOps Dashboard API",
    description="API for managing MLflow, Kubeflow Pipelines, and KServe deployments",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MLOps Dashboard API",
        "docs": "/docs",
    }

# Include routers
app.include_router(mlflow_routes.router)
app.include_router(kubeflow_routes.router)
app.include_router(kserve_routes.router)

# Event handlers
@app.on_event("startup")
async def startup_event():
    logger.info("Starting MLOps Dashboard API")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MLOps Dashboard API") 