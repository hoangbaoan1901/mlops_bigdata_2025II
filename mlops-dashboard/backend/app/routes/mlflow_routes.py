from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import asyncio

from ..models.base_models import MLflowConfig, ServerStatus
from ..services.mlflow_service import MLflowService
from ..services.mock_service import MockService

router = APIRouter(prefix="/mlflow", tags=["MLflow"])

# Dependencies
def get_mlflow_service():
    return MLflowService()

def get_mock_service():
    return MockService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Routes
@router.get("/status", response_model=ServerStatus)
async def get_mlflow_status(
    mlflow_service: MLflowService = Depends(get_mlflow_service)
):
    """Get MLflow server status"""
    return mlflow_service.get_status()

@router.post("/start")
async def start_mlflow(
    config: MLflowConfig,
    background_tasks: BackgroundTasks,
    mlflow_service: MLflowService = Depends(get_mlflow_service)
):
    """Start MLflow server"""
    if mlflow_service.mlflow_status == "running":
        return JSONResponse(
            status_code=400,
            content={"message": "MLflow server is already running"}
        )
    
    mlflow_service.start_server(config)
    
    return JSONResponse(
        status_code=202,
        content={
            "message": "Starting MLflow server",
            "config": config.dict()
        }
    )

@router.post("/stop")
async def stop_mlflow(
    mlflow_service: MLflowService = Depends(get_mlflow_service)
):
    """Stop MLflow server"""
    if mlflow_service.mlflow_status == "stopped":
        return JSONResponse(
            status_code=400,
            content={"message": "MLflow server is not running"}
        )
    
    try:
        mlflow_service.stop_server()
        return {"message": "MLflow server stopped successfully"}
    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=f"Error stopping MLflow server: {str(e)}"
        )

@router.get("/logs")
async def get_mlflow_logs(
    mlflow_service: MLflowService = Depends(get_mlflow_service)
):
    """Get MLflow server logs"""
    return {"logs": mlflow_service.get_logs()}

@router.websocket("/ws/logs")
async def websocket_mlflow_logs(
    websocket: WebSocket,
    mlflow_service: MLflowService = Depends(get_mlflow_service)
):
    """WebSocket for streaming MLflow logs"""
    await manager.connect(websocket)
    try:
        last_log_count = 0
        while True:
            logs = mlflow_service.get_logs()
            if len(logs) > last_log_count:
                new_logs = logs[last_log_count:]
                last_log_count = len(logs)
                await websocket.send_json({"logs": new_logs})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mock data routes
@router.get("/mock/experiments")
async def get_mock_mlflow_experiments(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock MLflow experiments"""
    return mock_service.get_mlflow_experiments()

@router.get("/mock/runs")
async def get_mock_mlflow_runs(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock MLflow runs"""
    return mock_service.get_mlflow_runs()

@router.get("/mock/models")
async def get_mock_mlflow_models(
    mock_service: MockService = Depends(get_mock_service)
):
    """Get mock MLflow registered models"""
    return mock_service.get_mlflow_models() 