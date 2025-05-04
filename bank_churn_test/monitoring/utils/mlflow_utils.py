#!/usr/bin/env python
import mlflow
import time
import uuid
import socket
from datetime import datetime
import sys
import os

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.mlflow_config import configure_mlflow, ensure_no_active_runs

def log_prediction_to_mlflow(data, prediction, experiment_name="bank-churn-inference", actual=None, run_id=None):
    """Log dữ liệu và kết quả dự đoán vào MLflow với nhiều metrics hơn"""
    # Cấu hình MLflow nếu cần
    mlflow = configure_mlflow(experiment_name)
    
    # Đảm bảo không có active run
    if not run_id:
        ensure_no_active_runs()
    
    # Tạo run mới hoặc sử dụng run hiện có
    if run_id:
        mlflow.start_run(run_id=run_id)
    else:
        mlflow.start_run()
    
    try:
        # Log thông tin về request
        mlflow.log_param("request_id", str(uuid.uuid4()))
        mlflow.log_param("timestamp", datetime.now().isoformat())
        mlflow.log_param("client_hostname", socket.gethostname())
        
        # Log chi tiết về model
        mlflow.log_param("model_name", prediction.get("model_name", "bankchurn"))
        mlflow.log_param("model_id", prediction.get("id", "unknown"))
        
        # Log input features với prefix để tổ chức tốt hơn
        for key, value in data.items():
            mlflow.log_param(f"feature.{key}", value)
        
        # Log các metrics về hiệu suất API
        mlflow.log_metric("api.response_time_ms", prediction.get("response_time", 0))
        mlflow.log_metric("api.request_size_bytes", prediction.get("request_size", 0))
        mlflow.log_metric("api.response_size_bytes", prediction.get("response_size", 0))
        mlflow.log_metric("api.status_code", prediction.get("status_code", 0))
        
        # Log kết quả dự đoán
        prediction_value = prediction["outputs"][0]["data"][0]
        mlflow.log_metric("prediction.value", prediction_value)
        mlflow.log_metric("prediction.confidence", 1.0)  # Placeholder, có thể thay đổi nếu model cung cấp confidence
        
        # Log thông tin về thời gian dự đoán
        current_time = time.time()
        mlflow.log_metric("time.epoch", current_time)
        mlflow.log_metric("time.hour_of_day", datetime.fromtimestamp(current_time).hour)
        mlflow.log_metric("time.day_of_week", datetime.fromtimestamp(current_time).weekday())
        
        # Log giá trị thực tế nếu có để tính metrics
        if actual is not None:
            mlflow.log_metric("actual.value", actual)
            is_correct = 1 if prediction_value == actual else 0
            mlflow.log_metric("evaluation.correct", is_correct)
            mlflow.log_metric("evaluation.error", 1 - is_correct)
        
        # Log thêm chi tiết thống kê về dữ liệu đầu vào
        numeric_features = {k: v for k, v in data.items() 
                            if isinstance(v, (int, float)) and k not in ["Geography", "Gender"]}
        
        if numeric_features:
            mlflow.log_metric("stats.mean_credit_score", data.get("CreditScore", 0))
            mlflow.log_metric("stats.age_standardized", (data.get("Age", 0) - 40) / 20)  # Giả sử trung bình tuổi là 40, std là 20
            
            # Z-score cho Balance (giả sử mean=60000, std=50000)
            balance_z = (data.get("Balance", 0) - 60000) / 50000
            mlflow.log_metric("stats.balance_z_score", balance_z)
            
            # Z-score cho EstimatedSalary (giả sử mean=100000, std=50000)
            salary_z = (data.get("EstimatedSalary", 0) - 100000) / 50000
            mlflow.log_metric("stats.salary_z_score", salary_z)
        
        # Log thêm một số feature flags
        mlflow.log_param("flags.high_value_customer", data.get("Balance", 0) > 100000 or data.get("EstimatedSalary", 0) > 150000)
        mlflow.log_param("flags.long_tenure", data.get("Tenure", 0) >= 5)
        mlflow.log_param("flags.multi_product", data.get("NumOfProducts", 0) > 1)
        
        # Tính và log thêm một số features phái sinh
        mlflow.log_metric("derived.balance_per_product", data.get("Balance", 0) / max(1, data.get("NumOfProducts", 1)))
        mlflow.log_metric("derived.balance_per_tenure_year", data.get("Balance", 0) / max(1, data.get("Tenure", 1)))
        
        return mlflow.active_run().info.run_id
    
    finally:
        mlflow.end_run()

def log_batch_summary(run_ids, predictions, experiment_name="bank-churn-batch"):
    """Log tổng kết về batch dự đoán"""
    # Cấu hình MLflow
    mlflow = configure_mlflow(experiment_name)
    
    # Đảm bảo không có active run
    ensure_no_active_runs()
    
    with mlflow.start_run(run_name="batch-summary"):
        # Log thông tin chung về batch
        mlflow.log_param("batch_id", str(uuid.uuid4()))
        mlflow.log_param("batch_timestamp", datetime.now().isoformat())
        mlflow.log_param("batch_size", len(predictions))
        mlflow.log_param("related_run_ids", ",".join(run_ids))
        
        # Tính các metrics tổng hợp
        prediction_values = [p["outputs"][0]["data"][0] for p in predictions]
        response_times = [p.get("response_time", 0) for p in predictions]
        
        # Log metrics về phân phối dự đoán
        churn_rate = sum(1 for v in prediction_values if v == 1) / len(prediction_values)
        mlflow.log_metric("batch.churn_rate", churn_rate)
        mlflow.log_metric("batch.non_churn_rate", 1 - churn_rate)
        
        # Log metrics về API performance
        import numpy as np
        mlflow.log_metric("batch.mean_response_time", np.mean(response_times))
        mlflow.log_metric("batch.median_response_time", np.median(response_times))
        mlflow.log_metric("batch.min_response_time", np.min(response_times))
        mlflow.log_metric("batch.max_response_time", np.max(response_times))
        mlflow.log_metric("batch.std_response_time", np.std(response_times))
        mlflow.log_metric("batch.p95_response_time", np.percentile(response_times, 95))
        mlflow.log_metric("batch.p99_response_time", np.percentile(response_times, 99))
        
        # Log thêm thông tin về thời gian
        current_time = time.time()
        mlflow.log_metric("batch.timestamp", current_time)
        mlflow.log_metric("batch.hour", datetime.fromtimestamp(current_time).hour)
        mlflow.log_metric("batch.day_of_week", datetime.fromtimestamp(current_time).weekday())
        mlflow.log_metric("batch.day_of_month", datetime.fromtimestamp(current_time).day)
        mlflow.log_metric("batch.month", datetime.fromtimestamp(current_time).month)

def get_experiment_runs(experiment_name, max_runs=100):
    """Get runs from an experiment"""
    mlflow = configure_mlflow(experiment_name)
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if not experiment:
        print(f"Experiment {experiment_name} not found")
        return None
    
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        max_results=max_runs
    )
    
    return runs

def force_terminate_run(run_id):
    """Force terminate a run using the REST API"""
    import requests
    import json
    from config.mlflow_config import MLFLOW_TRACKING_URI
    
    api_url = f"{MLFLOW_TRACKING_URI}/api/2.0/mlflow/runs/update"
    
    payload = {
        "run_id": run_id,
        "status": "FAILED",
        "end_time": int(time.time() * 1000)  # Current time in milliseconds
    }
    
    try:
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            print(f"Successfully force-terminated run {run_id}")
            return True
        else:
            print(f"Failed to force-terminate run. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error in force_terminate_run: {str(e)}")
        return False