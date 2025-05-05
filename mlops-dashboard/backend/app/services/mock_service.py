import logging
from typing import Dict, List, Any
import json
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MockService:
    """Service for generating mock data for development and testing"""
    
    def get_mlflow_experiments(self) -> Dict[str, Any]:
        """Get mock MLflow experiments
        
        Returns:
            Mock experiment data
        """
        return {
            "experiments": [
                {
                    "experiment_id": "1",
                    "name": "Bank Customer Churn Prediction",
                    "artifact_location": "mlflow-artifacts:/1",
                    "lifecycle_stage": "active",
                    "last_update_time": (datetime.now() - timedelta(days=2)).isoformat(),
                    "creation_time": (datetime.now() - timedelta(days=10)).isoformat(),
                    "tags": {
                        "project": "banking",
                        "team": "data-science"
                    }
                },
                {
                    "experiment_id": "2",
                    "name": "Credit Risk Assessment",
                    "artifact_location": "mlflow-artifacts:/2",
                    "lifecycle_stage": "active",
                    "last_update_time": (datetime.now() - timedelta(days=1)).isoformat(),
                    "creation_time": (datetime.now() - timedelta(days=5)).isoformat(),
                    "tags": {
                        "project": "risk",
                        "team": "risk-analytics"
                    }
                },
                {
                    "experiment_id": "3",
                    "name": "Customer Segmentation",
                    "artifact_location": "mlflow-artifacts:/3",
                    "lifecycle_stage": "active",
                    "last_update_time": datetime.now().isoformat(),
                    "creation_time": (datetime.now() - timedelta(days=3)).isoformat(),
                    "tags": {
                        "project": "marketing",
                        "team": "data-science"
                    }
                }
            ]
        }
    
    def get_mlflow_runs(self) -> Dict[str, Any]:
        """Get mock MLflow runs
        
        Returns:
            Mock run data
        """
        return {
            "runs": [
                {
                    "run_id": "run1",
                    "experiment_id": "1",
                    "status": "FINISHED",
                    "start_time": (datetime.now() - timedelta(days=2, hours=1)).timestamp() * 1000,
                    "end_time": (datetime.now() - timedelta(days=2)).timestamp() * 1000,
                    "metrics": {
                        "accuracy": 0.92,
                        "precision": 0.89,
                        "recall": 0.94,
                        "f1": 0.91
                    },
                    "params": {
                        "model_type": "RandomForest",
                        "n_estimators": "100",
                        "max_depth": "10"
                    },
                    "tags": {
                        "version": "v1.0",
                        "author": "data-scientist-1"
                    }
                },
                {
                    "run_id": "run2",
                    "experiment_id": "1",
                    "status": "FINISHED",
                    "start_time": (datetime.now() - timedelta(days=1, hours=2)).timestamp() * 1000,
                    "end_time": (datetime.now() - timedelta(days=1)).timestamp() * 1000,
                    "metrics": {
                        "accuracy": 0.94,
                        "precision": 0.92,
                        "recall": 0.95,
                        "f1": 0.93
                    },
                    "params": {
                        "model_type": "GradientBoosting",
                        "n_estimators": "150",
                        "learning_rate": "0.1"
                    },
                    "tags": {
                        "version": "v1.1",
                        "author": "data-scientist-2"
                    }
                },
                {
                    "run_id": "run3",
                    "experiment_id": "2",
                    "status": "RUNNING",
                    "start_time": (datetime.now() - timedelta(hours=5)).timestamp() * 1000,
                    "metrics": {
                        "auc": 0.88,
                        "accuracy": 0.91
                    },
                    "params": {
                        "model_type": "XGBoost",
                        "n_estimators": "200",
                        "learning_rate": "0.05"
                    },
                    "tags": {
                        "version": "v0.9",
                        "author": "data-scientist-3"
                    }
                }
            ]
        }
    
    def get_mlflow_models(self) -> Dict[str, Any]:
        """Get mock MLflow registered models
        
        Returns:
            Mock model data
        """
        return {
            "models": [
                {
                    "name": "churn-prediction",
                    "creation_timestamp": (datetime.now() - timedelta(days=10)).timestamp() * 1000,
                    "last_updated_timestamp": (datetime.now() - timedelta(days=1)).timestamp() * 1000,
                    "latest_versions": [
                        {
                            "name": "churn-prediction",
                            "version": "1",
                            "creation_timestamp": (datetime.now() - timedelta(days=10)).timestamp() * 1000,
                            "status": "Production",
                            "source": "s3://mlflow-models/churn-prediction/1",
                            "run_id": "run1"
                        },
                        {
                            "name": "churn-prediction",
                            "version": "2",
                            "creation_timestamp": (datetime.now() - timedelta(days=2)).timestamp() * 1000,
                            "status": "Staging",
                            "source": "s3://mlflow-models/churn-prediction/2",
                            "run_id": "run2"
                        }
                    ]
                },
                {
                    "name": "credit-risk",
                    "creation_timestamp": (datetime.now() - timedelta(days=5)).timestamp() * 1000,
                    "last_updated_timestamp": (datetime.now() - timedelta(hours=12)).timestamp() * 1000,
                    "latest_versions": [
                        {
                            "name": "credit-risk",
                            "version": "1",
                            "creation_timestamp": (datetime.now() - timedelta(days=5)).timestamp() * 1000,
                            "status": "Production",
                            "source": "s3://mlflow-models/credit-risk/1",
                            "run_id": "run3"
                        }
                    ]
                }
            ]
        }
    
    def get_kubeflow_pipelines(self) -> Dict[str, Any]:
        """Get mock Kubeflow pipelines
        
        Returns:
            Mock pipeline data
        """
        return {
            "pipelines": [
                {
                    "id": "pipe-1",
                    "name": "Bank Churn Pipeline",
                    "description": "Data processing and model training for bank churn prediction",
                    "created_at": (datetime.now() - timedelta(days=15)).isoformat()
                },
                {
                    "id": "pipe-2",
                    "name": "Credit Risk Pipeline",
                    "description": "End-to-end pipeline for credit risk assessment",
                    "created_at": (datetime.now() - timedelta(days=7)).isoformat()
                },
                {
                    "id": "pipe-3",
                    "name": "Customer Segmentation Pipeline",
                    "description": "Customer clustering and segmentation analysis",
                    "created_at": (datetime.now() - timedelta(days=3)).isoformat()
                }
            ]
        }
    
    def get_kubeflow_runs(self) -> Dict[str, Any]:
        """Get mock Kubeflow pipeline runs
        
        Returns:
            Mock pipeline run data
        """
        return {
            "runs": [
                {
                    "run_id": "run-001",
                    "pipeline_id": "pipe-1",
                    "run_name": "Bank Churn Pipeline Run #1",
                    "status": "Completed",
                    "start_time": (datetime.now() - timedelta(days=14)).isoformat(),
                    "end_time": (datetime.now() - timedelta(days=14, hours=2)).isoformat(),
                    "duration": "2h 10m",
                    "metrics": {
                        "accuracy": 0.91,
                        "data_processed": "10,000 records"
                    }
                },
                {
                    "run_id": "run-002",
                    "pipeline_id": "pipe-1",
                    "run_name": "Bank Churn Pipeline Run #2",
                    "status": "Completed",
                    "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
                    "end_time": (datetime.now() - timedelta(days=6, hours=22)).isoformat(),
                    "duration": "2h 5m",
                    "metrics": {
                        "accuracy": 0.93,
                        "data_processed": "12,000 records"
                    }
                },
                {
                    "run_id": "run-003",
                    "pipeline_id": "pipe-2",
                    "run_name": "Credit Risk Pipeline Run #1",
                    "status": "Running",
                    "start_time": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "duration": "5h+",
                    "metrics": {
                        "progress": "80%"
                    }
                },
                {
                    "run_id": "run-004",
                    "pipeline_id": "pipe-3",
                    "run_name": "Customer Segmentation Run #1",
                    "status": "Failed",
                    "start_time": (datetime.now() - timedelta(days=2)).isoformat(),
                    "end_time": (datetime.now() - timedelta(days=2, hours=1)).isoformat(),
                    "duration": "1h 12m",
                    "error": "Resource quota exceeded during model training",
                    "metrics": {
                        "progress": "65%"
                    }
                }
            ]
        }
    
    def get_kubeflow_pipeline_graph(self, pipeline_id: str = "pipe-2") -> Dict[str, Any]:
        """Get mock Kubeflow pipeline graph
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            Mock pipeline graph data
        """
        return {
            "nodes": [
                {
                    "id": "node-1",
                    "name": "Data Loading",
                    "type": "DataIO",
                    "status": "Completed"
                },
                {
                    "id": "node-2",
                    "name": "Data Validation",
                    "type": "DataValidation",
                    "status": "Completed"
                },
                {
                    "id": "node-3",
                    "name": "Feature Engineering",
                    "type": "FeatureExtraction",
                    "status": "Completed"
                },
                {
                    "id": "node-4",
                    "name": "Model Training",
                    "type": "ModelTraining",
                    "status": "Running"
                },
                {
                    "id": "node-5",
                    "name": "Model Evaluation",
                    "type": "ModelEvaluation",
                    "status": "Waiting"
                },
                {
                    "id": "node-6",
                    "name": "Model Deployment",
                    "type": "ModelDeployment",
                    "status": "Waiting"
                }
            ],
            "edges": [
                {"source": "node-1", "target": "node-2"},
                {"source": "node-2", "target": "node-3"},
                {"source": "node-3", "target": "node-4"},
                {"source": "node-4", "target": "node-5"},
                {"source": "node-5", "target": "node-6"}
            ]
        }
    
    def get_kserve_deployments(self) -> Dict[str, Any]:
        """Get mock KServe deployments
        
        Returns:
            Mock KServe deployment data
        """
        return {
            "deployments": [
                {
                    "name": "churn-model",
                    "namespace": "bankchurn-kserve-2",
                    "created": (datetime.now() - timedelta(days=5)).isoformat(),
                    "model_uri": "s3://mlflow-models/churn-prediction/1",
                    "framework": "tensorflow",
                    "version": "v1",
                    "status": "Ready",
                    "endpoint": "http://churn-model.bankchurn-kserve-2.example.com/v1/models/churn-model",
                    "replicas": 2,
                    "resources": {
                        "cpu": "1",
                        "memory": "2Gi"
                    },
                    "traffic": 100
                },
                {
                    "name": "credit-risk-model",
                    "namespace": "bankchurn-kserve-2",
                    "created": (datetime.now() - timedelta(days=2)).isoformat(),
                    "model_uri": "s3://mlflow-models/credit-risk/1",
                    "framework": "sklearn",
                    "version": "v1",
                    "status": "Ready",
                    "endpoint": "http://credit-risk-model.bankchurn-kserve-2.example.com/v1/models/credit-risk-model",
                    "replicas": 1,
                    "resources": {
                        "cpu": "500m",
                        "memory": "1Gi"
                    },
                    "traffic": 100
                },
                {
                    "name": "customer-segmentation",
                    "namespace": "default",
                    "created": (datetime.now() - timedelta(hours=12)).isoformat(),
                    "model_uri": "s3://mlflow-models/segmentation/1",
                    "framework": "pytorch",
                    "version": "v1",
                    "status": "Not Ready: waiting for container readiness",
                    "endpoint": "",
                    "replicas": 1,
                    "resources": {
                        "cpu": "2",
                        "memory": "4Gi"
                    },
                    "traffic": 100,
                    "error": "Image pull backoff: failed to pull image pytorch:latest"
                }
            ]
        }
    
    def get_kserve_serving_runtimes(self) -> Dict[str, Any]:
        """Get mock KServe serving runtimes
        
        Returns:
            Mock serving runtime data
        """
        return {
            "runtimes": [
                {
                    "name": "sklearn-runtime",
                    "namespace": "kserve-system",
                    "created": (datetime.now() - timedelta(days=30)).isoformat(),
                    "version": "v1",
                    "frameworks": ["sklearn"],
                    "protocols": ["v1", "v2"]
                },
                {
                    "name": "tensorflow-runtime",
                    "namespace": "kserve-system",
                    "created": (datetime.now() - timedelta(days=30)).isoformat(),
                    "version": "v1",
                    "frameworks": ["tensorflow"],
                    "protocols": ["v1", "v2"]
                },
                {
                    "name": "pytorch-runtime",
                    "namespace": "kserve-system",
                    "created": (datetime.now() - timedelta(days=30)).isoformat(),
                    "version": "v1",
                    "frameworks": ["pytorch"],
                    "protocols": ["v1", "v2"]
                },
                {
                    "name": "xgboost-runtime",
                    "namespace": "kserve-system",
                    "created": (datetime.now() - timedelta(days=30)).isoformat(),
                    "version": "v1",
                    "frameworks": ["xgboost"],
                    "protocols": ["v1", "v2"]
                }
            ]
        } 