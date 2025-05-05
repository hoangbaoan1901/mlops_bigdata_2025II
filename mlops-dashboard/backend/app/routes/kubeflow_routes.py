from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any

from ..models.base_models import KubeflowConfig
from ..services.kubeflow_service import KubeflowService
from ..services.mock_service import MockService

router = APIRouter(prefix="/kubeflow", tags=["Kubeflow"])

# Dependencies
def get_kubeflow_service():
    return KubeflowService()

def get_mock_service():
    return MockService()

# Routes
@router.get("/port-forward-command")
async def get_kubeflow_port_forward_command(
    config: KubeflowConfig,
    kubeflow_service: KubeflowService = Depends(get_kubeflow_service)
):
    """Get Kubeflow port-forward command"""
    command = kubeflow_service.get_port_forward_command(
        namespace=config.namespace,
        service=config.service,
        port=config.port
    )
    return {"command": command}

@router.get("/check-connection")
async def check_kubeflow_connection(
    port: int = 8080,
    kubeflow_service: KubeflowService = Depends(get_kubeflow_service)
):
    """Check Kubeflow connection status"""
    return kubeflow_service.check_connection(port)

# Mock data routes
@router.get("/mock/pipelines")
async def get_mock_kubeflow_pipelines(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock Kubeflow pipelines"""
    return mock_service.get_kubeflow_pipelines()

@router.get("/mock/runs")
async def get_mock_kubeflow_runs(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock Kubeflow pipeline runs"""
    return mock_service.get_kubeflow_runs()

@router.get("/mock/pipeline-graph")
async def get_mock_pipeline_graph(
    pipeline_id: str = "pipe-2",
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock Kubeflow pipeline graph"""
    return mock_service.get_kubeflow_pipeline_graph(pipeline_id) 