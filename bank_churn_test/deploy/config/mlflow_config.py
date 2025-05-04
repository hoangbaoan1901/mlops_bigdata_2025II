#!/usr/bin/env python
import os

# MLflow configuration
MLFLOW_TRACKING_URI = "http://localhost:5000"
MINIO_ENDPOINT = "http://minio-service.kubeflow.svc.cluster.local:9000"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "mlflow-artifacts"

# KServe configuration
KSERVE_ENDPOINT = "http://localhost:8085"
MODEL_NAME = "bankchurn"

def configure_mlflow(experiment_name="bank-churn-default"):
    """Configure MLflow tracking with MinIO as artifact store
    
    Args:
        experiment_name: Name of the MLflow experiment
    """
    # Set MinIO credentials
    os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ACCESS_KEY
    os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_SECRET_KEY
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT
    
    # Configure MLflow
    import mlflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Create or set experiment
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location=f"s3://{MINIO_BUCKET}/{experiment_name}"
            )
            print(f"Created new experiment '{experiment_name}' with ID: {experiment_id}")
        else:
            mlflow.set_experiment(experiment_name)
            print(f"Using existing experiment '{experiment_name}' with ID: {experiment.experiment_id}")
    except Exception as e:
        print(f"Error setting up experiment: {str(e)}")
        # Fallback to just setting the experiment
        mlflow.set_experiment(experiment_name)
    
    return mlflow

def ensure_no_active_runs():
    """End any active MLflow runs to prevent issues"""
    import mlflow
    try:
        mlflow.end_run()
        print("Cleared any active MLflow runs")
    except Exception as e:
        print(f"Note when clearing runs: {str(e)}") 