#!/usr/bin/env python
import requests
import json
import time
import sys
import os

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.mlflow_config import KSERVE_ENDPOINT, MODEL_NAME

def get_model_metadata():
    """Lấy metadata của model từ KServe"""
    url = f"{KSERVE_ENDPOINT}/v2/models/{MODEL_NAME}"
    start_time = time.time()
    response = requests.get(url)
    response_time = (time.time() - start_time) * 1000  # Convert to ms
    return response.json(), response_time

def predict_churn(data):
    """Dự đoán churn với KServe API"""
    url = f"{KSERVE_ENDPOINT}/v2/models/{MODEL_NAME}/infer"
    headers = {"Content-Type": "application/json"}
    
    # Chuyển đổi data thành định dạng KServe input
    inputs = []
    for key, value in data.items():
        inputs.append({
            "name": key,
            "shape": [1],
            "datatype": "FP64",
            "data": [value]
        })
    
    payload = {"inputs": inputs}
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        result = response.json()
        result["response_time"] = response_time
        result["request_size"] = len(json.dumps(payload))
        result["response_size"] = len(response.text)
        result["status_code"] = response.status_code
        result["error"] = None
        result["success"] = True
        
        return result
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return {
            "error": str(e),
            "response_time": response_time,
            "status_code": 500,
            "success": False
        }

def check_model_health():
    """Kiểm tra model có hoạt động không"""
    url = f"{KSERVE_ENDPOINT}/v2/models/{MODEL_NAME}"
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status_code": response.status_code,
            "response_time": response_time,
            "is_healthy": response.status_code == 200,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status_code": 500,
            "response_time": None,
            "is_healthy": False,
            "error": str(e),
            "timestamp": time.time()
        }

def generate_test_data(count=10):
    """Tạo dữ liệu test ngẫu nhiên"""
    import numpy as np
    test_data = []
    
    for _ in range(count):
        data = {
            "CreditScore": np.random.randint(300, 900),
            "Geography": np.random.randint(0, 3),
            "Gender": np.random.randint(0, 2),
            "Age": np.random.randint(18, 95),
            "Tenure": np.random.randint(0, 11),
            "Balance": np.random.randint(0, 250000),
            "NumOfProducts": np.random.randint(1, 5),
            "HasCrCard": np.random.randint(0, 2),
            "IsActiveMember": np.random.randint(0, 2),
            "EstimatedSalary": np.random.randint(10000, 200000)
        }
        test_data.append(data)
    
    return test_data 