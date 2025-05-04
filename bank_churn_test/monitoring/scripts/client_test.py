#!/usr/bin/env python
import sys
import os
import time
from datetime import datetime

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.mlflow_config import configure_mlflow, ensure_no_active_runs
from utils.kserve_client import get_model_metadata, predict_churn, generate_test_data
from utils.mlflow_utils import log_prediction_to_mlflow, log_batch_summary

def main():
    print("Cấu hình MLflow...")
    mlflow = configure_mlflow("bank-churn-inference")
    ensure_no_active_runs()
    
    print("Kiểm tra model metadata...")
    model_metadata, metadata_response_time = get_model_metadata()
    print(f"Model: {model_metadata['name']}")
    print(f"Inputs: {len(model_metadata['inputs'])}")
    print(f"Metadata response time: {metadata_response_time:.2f} ms")
    
    # Log thông tin về model metadata
    with mlflow.start_run(run_name="model-metadata"):
        mlflow.log_param("model_name", model_metadata['name'])
        mlflow.log_param("model_platform", model_metadata.get('platform', 'unknown'))
        mlflow.log_param("inputs_count", len(model_metadata['inputs']))
        mlflow.log_param("outputs_count", len(model_metadata.get('outputs', [])))
        mlflow.log_metric("metadata_response_time_ms", metadata_response_time)
    
    # Số lượng mẫu test
    print("\nTạo dữ liệu test và thực hiện dự đoán...")
    test_data = generate_test_data(20)
    
    predictions = []
    run_ids = []
    
    for i, data in enumerate(test_data):
        print(f"\nDự đoán {i+1}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        
        # Thực hiện dự đoán
        try:
            prediction = predict_churn(data)
            prediction_value = prediction["outputs"][0]["data"][0]
            print(f"  Kết quả dự đoán: {prediction_value} (1=Churn, 0=Không churn)")
            print(f"  Thời gian phản hồi: {prediction['response_time']:.2f} ms")
            
            # Log vào MLflow
            run_id = log_prediction_to_mlflow(data, prediction)
            run_ids.append(run_id)
            predictions.append(prediction)
            print(f"  Đã log dự đoán vào MLflow với Run ID: {run_id}")
            
        except Exception as e:
            print(f"  Lỗi khi dự đoán: {str(e)}")
    
    # Log tổng kết về batch
    if predictions:
        print("\nLog tổng kết batch...")
        log_batch_summary(run_ids, predictions)
        print("Hoàn thành!")

if __name__ == "__main__":
    main()