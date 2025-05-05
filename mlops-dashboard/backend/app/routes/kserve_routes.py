from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional

from ..models.base_models import KServeDeploymentConfig
from ..services.kserve_service import KServeService
from ..services.mock_service import MockService

router = APIRouter(prefix="/kserve", tags=["KServe"])

# Dependencies
def get_kserve_service():
    return KServeService()

def get_mock_service():
    return MockService()

# Routes
@router.get("/deployments")
async def get_kserve_deployments(
    namespace: Optional[str] = None,
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get all KServe deployments across namespaces
    
    Args:
        namespace: Optional, filter by specific namespace
    """
    return {"deployments": kserve_service.get_inference_services(namespace)}

@router.get("/deployments/{name}")
async def get_kserve_deployment(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get a specific KServe deployment
    
    Args:
        name: Name of the InferenceService
        namespace: Kubernetes namespace
    """
    deployment = kserve_service.get_inference_service(name, namespace)
    if not deployment:
        raise HTTPException(
            status_code=404,
            detail=f"InferenceService {name} not found in namespace {namespace}"
        )
    return {"deployment": deployment}

@router.post("/deployments")
async def create_kserve_deployment(
    config: KServeDeploymentConfig,
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Create a new KServe deployment"""
    try:
        deployment = kserve_service.create_inference_service(config.dict())
        return {"deployment": deployment, "message": "Deployment created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating deployment: {str(e)}"
        )

@router.delete("/deployments/{name}")
async def delete_kserve_deployment(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Delete a KServe deployment
    
    Args:
        name: Name of the InferenceService
        namespace: Kubernetes namespace
    """
    success = kserve_service.delete_inference_service(name, namespace)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Error deleting InferenceService {name} in namespace {namespace}"
        )
    return {"message": f"InferenceService {name} in namespace {namespace} deleted successfully"}

@router.get("/deployments/{name}/logs")
async def get_kserve_logs(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get logs for a KServe deployment
    
    Args:
        name: Name of the InferenceService
        namespace: Kubernetes namespace
    """
    logs = kserve_service.get_inference_service_logs(name, namespace)
    return {"logs": logs}

@router.get("/serving-runtimes")
async def get_serving_runtimes(
    namespace: Optional[str] = None,
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get all KServe serving runtimes
    
    Args:
        namespace: Optional, filter by specific namespace
    """
    return {"runtimes": kserve_service.get_serving_runtimes(namespace)}

@router.get("/deployments/{name}/pods")
async def get_kserve_deployment_pods(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get pods for a KServe deployment
    
    Args:
        name: Name of the InferenceService
        namespace: Kubernetes namespace
    """
    pods = kserve_service.get_pod_details(name, namespace)
    return {"pods": pods}

@router.get("/pods")
async def get_kserve_pods(
    namespace: Optional[str] = "bankchurn-kserve-2",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get all pods in a namespace
    
    Args:
        namespace: Kubernetes namespace
    """
    pods = kserve_service.get_all_pods(namespace)
    return {"pods": pods}

# Mock data routes
@router.get("/mock/deployments")
async def get_mock_kserve_deployments(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock KServe deployments"""
    return mock_service.get_kserve_deployments()

@router.get("/mock/serving-runtimes")
async def get_mock_serving_runtimes(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock KServe serving runtimes"""
    return mock_service.get_kserve_serving_runtimes() 