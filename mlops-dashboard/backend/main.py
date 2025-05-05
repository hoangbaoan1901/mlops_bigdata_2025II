from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess
import requests
import threading
import time
import asyncio
import logging
import json
import os
from typing import List, Dict, Optional, Any, Union

# Import KServeService
from kserve_service import KServeService

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(
    title="MLOps Dashboard API",
    description="API để quản lý và hiển thị giao diện của MLflow và Kubeflow Pipelines",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production, giới hạn origin cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class MLflowConfig(BaseModel):
    port: int = 5000
    host: str = "0.0.0.0"
    artifact_uri: str = "./mlruns"
    backend_store_uri: Optional[str] = None

class KubeflowConfig(BaseModel):
    port: int = 8080
    namespace: str = "kubeflow"
    service: str = "ml-pipeline-ui"

class ServerStatus(BaseModel):
    status: str
    url: Optional[str] = None
    message: Optional[str] = None

class KServeDeploymentConfig(BaseModel):
    name: str
    namespace: str = "default"
    model_uri: str
    framework: str = "tensorflow"
    replicas: int = 1
    serviceAccountName: Optional[str] = None
    resources: Dict[str, str] = {
        "cpu": "1",
        "memory": "2Gi"
    }

# Lưu trữ trạng thái server và logs
mlflow_process = None
mlflow_status = "stopped"
mlflow_logs = []
connected_clients = []

# Dependency for KServe service
def get_kserve_service():
    return KServeService()

# WebSocket Manager
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

# API Routes
@app.get("/")
async def read_root():
    return {
        "message": "MLOps Dashboard API",
        "docs": "/docs",
        "status": {
            "mlflow": mlflow_status
        }
    }

# MLflow Routes
@app.get("/mlflow/status", response_model=ServerStatus)
async def get_mlflow_status():
    global mlflow_status
    
    if mlflow_status == "running":
        return ServerStatus(
            status=mlflow_status,
            url=f"http://localhost:{mlflow_config.port}",
            message="MLflow server is running"
        )
    else:
        return ServerStatus(
            status=mlflow_status,
            message="MLflow server is not running"
        )

@app.post("/mlflow/start")
async def start_mlflow(config: MLflowConfig, background_tasks: BackgroundTasks):
    global mlflow_process, mlflow_status, mlflow_logs, mlflow_config
    
    if mlflow_status == "running":
        return JSONResponse(
            status_code=400,
            content={"message": "MLflow server is already running"}
        )
    
    mlflow_config = config
    background_tasks.add_task(start_mlflow_server, config)
    
    return JSONResponse(
        status_code=202,
        content={
            "message": "Starting MLflow server",
            "config": config.dict()
        }
    )

@app.post("/mlflow/stop")
async def stop_mlflow():
    global mlflow_process, mlflow_status
    
    if mlflow_status == "stopped":
        return JSONResponse(
            status_code=400,
            content={"message": "MLflow server is not running"}
        )
    
    try:
        mlflow_process.terminate()
        mlflow_process.wait()
        mlflow_process = None
        mlflow_status = "stopped"
        
        return {"message": "MLflow server stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping MLflow server: {str(e)}")
        return HTTPException(
            status_code=500,
            detail=f"Error stopping MLflow server: {str(e)}"
        )

@app.get("/mlflow/logs")
async def get_mlflow_logs():
    global mlflow_logs
    return {"logs": mlflow_logs}

# Kubeflow Routes
@app.get("/kubeflow/port-forward-command")
async def get_kubeflow_port_forward_command(config: KubeflowConfig):
    command = f"kubectl port-forward -n {config.namespace} svc/{config.service} {config.port}:80"
    return {"command": command}

@app.get("/kubeflow/check-connection")
async def check_kubeflow_connection(port: int = 8080):
    try:
        response = requests.get(f"http://localhost:{port}/", timeout=2)
        if response.status_code == 200:
            return {"connected": True, "url": f"http://localhost:{port}/"}
        else:
            return {"connected": False, "error": f"Received status code {response.status_code}"}
    except Exception as e:
        return {"connected": False, "error": str(e)}

# KServe Routes
@app.get("/kserve/deployments")
async def get_kserve_deployments(
    namespace: Optional[str] = None,
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get all KServe deployments across namespaces
    
    Args:
        namespace: Optional, filter by specific namespace
    """
    try:
        deployments = kserve_service.get_inference_services(namespace)
        return {"deployments": deployments, "total": len(deployments)}
    except Exception as e:
        logger.error(f"Error getting KServe deployments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kserve/deployments/{name}")
async def get_kserve_deployment(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get a specific KServe deployment"""
    try:
        deployment = kserve_service.get_inference_service(name, namespace)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment {name} not found")
        return deployment
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting KServe deployment {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/kserve/deployments")
async def create_kserve_deployment(
    config: KServeDeploymentConfig,
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Create a new KServe deployment"""
    try:
        deployment = kserve_service.create_inference_service(config.dict())
        return deployment
    except Exception as e:
        logger.error(f"Error creating KServe deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/kserve/deployments/{name}")
async def delete_kserve_deployment(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Delete a KServe deployment"""
    try:
        success = kserve_service.delete_inference_service(name, namespace)
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to delete deployment {name}")
        return {"message": f"Deployment {name} deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting KServe deployment {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kserve/deployments/{name}/logs")
async def get_kserve_logs(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get logs for a KServe deployment"""
    try:
        logs = kserve_service.get_inference_service_logs(name, namespace)
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs for KServe deployment {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kserve/serving-runtimes")
async def get_serving_runtimes(
    namespace: Optional[str] = None,
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get all KServe serving runtimes"""
    try:
        runtimes = kserve_service.get_serving_runtimes(namespace)
        return {"runtimes": runtimes, "total": len(runtimes)}
    except Exception as e:
        logger.error(f"Error getting KServe serving runtimes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kserve/deployments/{name}/pods")
async def get_kserve_deployment_pods(
    name: str, 
    namespace: Optional[str] = "default",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get pod details for a KServe deployment"""
    try:
        pods = kserve_service.get_pod_details(name, namespace)
        if not pods:
            # Thử lấy pod từ namespace bankchurn-kserve-2 nếu không tìm thấy trong namespace hiện tại
            if namespace != "bankchurn-kserve-2":
                pods = kserve_service.get_pod_details(name, "bankchurn-kserve-2")
        return {"pods": pods, "total": len(pods)}
    except Exception as e:
        logger.error(f"Error getting pods for KServe deployment {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kserve/pods")
async def get_kserve_pods(
    namespace: Optional[str] = "bankchurn-kserve-2",
    kserve_service: KServeService = Depends(get_kserve_service)
):
    """Get all pods in a namespace, including KServe deployments and MLflow pods"""
    try:
        pods = kserve_service.get_all_pods(namespace)
        return {"pods": pods, "total": len(pods)}
    except Exception as e:
        logger.error(f"Error getting pods in namespace {namespace}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mock APIs for demo purposes
@app.get("/mock/mlflow/experiments")
async def get_mock_mlflow_experiments():
    return {
        "experiments": [
            {"id": "1", "name": "Default", "artifact_location": "./mlruns/1", "runs": 5},
            {"id": "2", "name": "Bank Churn Model", "artifact_location": "./mlruns/2", "runs": 12},
            {"id": "3", "name": "Stock Price Prediction", "artifact_location": "./mlruns/3", "runs": 8}
        ],
        "total": 3
    }

@app.get("/mock/mlflow/runs")
async def get_mock_mlflow_runs():
    return {
        "runs": [
            {
                "run_id": "abc123",
                "experiment_id": "2",
                "model": "RandomForest",
                "status": "COMPLETED",
                "metrics": {"accuracy": 0.92, "precision": 0.89, "recall": 0.91},
                "start_time": "2023-05-01T10:30:00Z"
            },
            {
                "run_id": "def456",
                "experiment_id": "3",
                "model": "XGBoost",
                "status": "RUNNING",
                "metrics": {"loss": 0.15, "val_loss": 0.18},
                "start_time": "2023-05-02T14:15:00Z"
            },
            {
                "run_id": "ghi789",
                "experiment_id": "1",
                "model": "NeuralNetwork",
                "status": "COMPLETED",
                "metrics": {"f1": 0.89, "auc": 0.95},
                "start_time": "2023-04-28T09:00:00Z"
            }
        ],
        "total": 3
    }

@app.get("/mock/mlflow/models")
async def get_mock_mlflow_models():
    return {
        "models": [
            {
                "name": "customer_churn_predictor",
                "version": "3",
                "stage": "Production",
                "last_updated": "2023-05-01T10:30:00Z"
            },
            {
                "name": "sales_forecaster",
                "version": "2",
                "stage": "Staging",
                "last_updated": "2023-04-28T14:15:00Z"
            }
        ],
        "total": 2
    }

@app.get("/mock/kubeflow/pipelines")
async def get_mock_kubeflow_pipelines():
    return {
        "pipelines": [
            {"id": "pipe-1", "name": "Data Processing Pipeline", "description": "Clean and process data", "created_at": "2023-04-01T10:00:00Z"},
            {"id": "pipe-2", "name": "Model Training Pipeline", "description": "Train ML model", "created_at": "2023-04-15T11:30:00Z"},
            {"id": "pipe-3", "name": "Model Deployment Pipeline", "description": "Deploy model to production", "created_at": "2023-04-20T09:45:00Z"},
            {"id": "pipe-4", "name": "Feature Engineering Pipeline", "description": "Create model features", "created_at": "2023-04-10T14:20:00Z"},
            {"id": "pipe-5", "name": "Model Evaluation Pipeline", "description": "Evaluate model performance", "created_at": "2023-04-18T16:15:00Z"}
        ],
        "total": 5
    }

@app.get("/mock/kubeflow/runs")
async def get_mock_kubeflow_runs():
    return {
        "runs": [
            {
                "run_name": "Train-2023-05-01",
                "pipeline_id": "pipe-2",
                "status": "Completed",
                "start_time": "2023-05-01T10:30:00Z",
                "end_time": "2023-05-01T11:15:00Z",
                "duration": "45m"
            },
            {
                "run_name": "Deploy-2023-04-30",
                "pipeline_id": "pipe-3",
                "status": "Running",
                "start_time": "2023-04-30T14:15:00Z",
                "end_time": None,
                "duration": "Running"
            },
            {
                "run_name": "Train-2023-04-29",
                "pipeline_id": "pipe-2",
                "status": "Failed",
                "start_time": "2023-04-29T09:00:00Z",
                "end_time": "2023-04-29T09:15:00Z",
                "duration": "15m",
                "error": "Out of memory error"
            }
        ],
        "total": 3
    }

@app.get("/mock/kubeflow/pipeline-graph")
async def get_mock_pipeline_graph(pipeline_id: str = "pipe-2"):
    nodes = [
        {"id": "node-1", "name": "Data Preparation", "type": "data", "status": "Completed"},
        {"id": "node-2", "name": "Feature Engineering", "type": "processing", "status": "Completed"},
        {"id": "node-3", "name": "Model Training", "type": "training", "status": "Completed"},
        {"id": "node-4", "name": "Model Evaluation", "type": "evaluation", "status": "Completed"},
        {"id": "node-5", "name": "Model Deployment", "type": "deployment", "status": "Running"}
    ]
    
    edges = [
        {"source": "node-1", "target": "node-2"},
        {"source": "node-2", "target": "node-3"},
        {"source": "node-3", "target": "node-4"},
        {"source": "node-4", "target": "node-5"}
    ]
    
    return {
        "pipeline_id": pipeline_id,
        "nodes": nodes,
        "edges": edges
    }

@app.get("/mock/kserve/deployments")
async def get_mock_kserve_deployments():
    """Mock API for KServe deployments"""
    return {
        "deployments": [
            {
                "name": "customer-churn-predictor",
                "namespace": "default",
                "model_uri": "s3://mlflow-models/customer_churn_predictor/production",
                "framework": "sklearn",
                "version": "3",
                "created": "2023-05-01T10:30:00Z",
                "status": "Running",
                "endpoint": "http://customer-churn-predictor.default.example.com/v1/models/customer-churn-predictor",
                "replicas": 2,
                "traffic": 100,
                "resources": {
                    "cpu": "1",
                    "memory": "2Gi"
                }
            },
            {
                "name": "bankchurn",
                "namespace": "bankchurn-kserve-2",
                "model_uri": "s3://mlflow-artifacts/3/3cad7a3d97dc44c4a07ef03680442b79/artifacts/model/",
                "framework": "mlflow",
                "version": "1",
                "created": "2023-06-10T15:20:00Z",
                "status": "Running",
                "endpoint": "http://bankchurn.bankchurn-kserve-2.example.com/v2/models/bankchurn",
                "replicas": 1,
                "traffic": 100,
                "serviceAccountName": "sa-minio-kserve",
                "resources": {
                    "cpu": "1",
                    "memory": "2Gi"
                }
            },
            {
                "name": "fraud-detection",
                "namespace": "default",
                "model_uri": "s3://mlflow-models/fraud_detection/production",
                "framework": "xgboost",
                "version": "2",
                "created": "2023-04-15T09:20:00Z",
                "status": "Running",
                "endpoint": "http://fraud-detection.default.example.com/v1/models/fraud-detection",
                "replicas": 3,
                "traffic": 100,
                "resources": {
                    "cpu": "2",
                    "memory": "4Gi"
                }
            },
            {
                "name": "image-classifier",
                "namespace": "computer-vision",
                "model_uri": "s3://mlflow-models/image_classifier/staging",
                "framework": "tensorflow",
                "version": "1",
                "created": "2023-04-01T14:10:00Z",
                "status": "Failed",
                "endpoint": "http://image-classifier.computer-vision.example.com/v1/models/image-classifier",
                "replicas": 0,
                "traffic": 0,
                "resources": {
                    "cpu": "4",
                    "memory": "8Gi",
                    "gpu": "1"
                },
                "error": "Resource quota exceeded"
            }
        ],
        "total": 4
    }

@app.get("/mock/kserve/serving-runtimes")
async def get_mock_serving_runtimes():
    """Mock API for KServe serving runtimes"""
    return {
        "runtimes": [
            {
                "name": "sklearn-server",
                "framework": "sklearn",
                "version": "latest",
                "status": "Available"
            },
            {
                "name": "tensorflow-serving",
                "framework": "tensorflow",
                "version": "2.6.0",
                "status": "Available"
            },
            {
                "name": "pytorch-server",
                "framework": "pytorch",
                "version": "1.9.0",
                "status": "Available"
            },
            {
                "name": "xgboost-server",
                "framework": "xgboost",
                "version": "1.5.0",
                "status": "Available"
            }
        ],
        "total": 4
    }

# WebSocket for real-time logs
@app.websocket("/ws/mlflow/logs")
async def websocket_mlflow_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send existing logs when connecting
        await websocket.send_text(json.dumps({"logs": mlflow_logs}))
        
        # Keep connection open
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Functions
def start_mlflow_server(config: MLflowConfig):
    global mlflow_process, mlflow_status, mlflow_logs
    
    cmd_parts = [
        "mlflow", "server",
        "--host", config.host,
        "--port", str(config.port),
        "--default-artifact-root", config.artifact_uri
    ]
    
    if config.backend_store_uri:
        cmd_parts.extend(["--backend-store-uri", config.backend_store_uri])
    
    command = " ".join(cmd_parts)
    logger.info(f"Starting MLflow server with command: {command}")
    
    try:
        mlflow_logs.clear()
        mlflow_process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        mlflow_status = "running"
        
        # Đọc và lưu logs
        while mlflow_process.poll() is None:
            output = mlflow_process.stderr.readline()
            if output:
                log_entry = output.strip()
                mlflow_logs.append(log_entry)
                # Limit log size
                if len(mlflow_logs) > 100:
                    mlflow_logs = mlflow_logs[-100:]
                # Broadcast log via WebSocket
                asyncio.run(manager.broadcast(json.dumps({"log": log_entry})))
        
        # Cập nhật trạng thái khi kết thúc
        mlflow_status = "stopped"
        logger.info("MLflow server stopped")
    except Exception as e:
        mlflow_status = "error"
        error_message = f"Error starting MLflow server: {str(e)}"
        logger.error(error_message)
        mlflow_logs.append(error_message)
        asyncio.run(manager.broadcast(json.dumps({"error": error_message})))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 