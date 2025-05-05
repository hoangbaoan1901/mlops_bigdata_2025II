from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union

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