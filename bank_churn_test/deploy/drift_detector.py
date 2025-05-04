#!/usr/bin/env python
import requests
import json
import mlflow
import os
import numpy as np
import pandas as pd
import time
from datetime import datetime
import threading
import schedule
from sklearn.metrics import f1_score, accuracy_score
from scipy.stats import ks_2samp
import pickle
import joblib
import io
import boto3
from botocore.client import Config

# Cấu hình MLflow
MLFLOW_TRACKING_URI = "http://mlflow.mlflow.svc.cluster.local:5000"
MINIO_ENDPOINT = "http://minio-service.kubeflow.svc.cluster.local:9000"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "mlflow-artifacts"

# Cấu hình KServe
KSERVE_ENDPOINT = "http://localhost:8085"
MODEL_NAME = "bankchurn"

# Cấu hình drift detection
DRIFT_DETECTION_INTERVAL_HOURS = 1  # Thực hiện mỗi 1 giờ
REFERENCE_DATA_SIZE = 100
CURRENT_DATA_SIZE = 50
PSI_THRESHOLD = 0.2  # Population Stability Index threshold
KS_THRESHOLD = 0.1  # Kolmogorov-Smirnov threshold

def configure_mlflow():
    """Cấu hình MLflow tracking"""
    os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ACCESS_KEY
    os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_SECRET_KEY
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("bank-churn-drift-detection")

def get_minio_client():
    """Khởi tạo MinIO client"""
    client = boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    return client

def generate_data(count=100):
    """Tạo dữ liệu ngẫu nhiên"""
    data = pd.DataFrame({
        "CreditScore": np.random.randint(300, 900, count),
        "Geography": np.random.randint(0, 3, count),
        "Gender": np.random.randint(0, 2, count),
        "Age": np.random.randint(18, 95, count),
        "Tenure": np.random.randint(0, 11, count),
        "Balance": np.random.randint(0, 250000, count),
        "NumOfProducts": np.random.randint(1, 5, count),
        "HasCrCard": np.random.randint(0, 2, count),
        "IsActiveMember": np.random.randint(0, 2, count),
        "EstimatedSalary": np.random.randint(10000, 200000, count)
    })
    
    return data

def get_reference_data():
    """Lấy dữ liệu tham chiếu từ MinIO hoặc tạo mới nếu chưa có"""
    s3_client = get_minio_client()
    try:
        # Thử lấy từ MinIO
        response = s3_client.get_object(Bucket=MINIO_BUCKET, Key='reference_data.pkl')
        reference_data = pickle.loads(response['Body'].read())
        print("Đã lấy dữ liệu tham chiếu từ MinIO")
        return reference_data
    except:
        # Nếu không tìm thấy, tạo mới
        print("Dữ liệu tham chiếu không tồn tại, tạo mới...")
        reference_data = generate_data(REFERENCE_DATA_SIZE)
        
        # Lưu vào MinIO
        with io.BytesIO() as bio:
            pickle.dump(reference_data, bio)
            bio.seek(0)
            s3_client.upload_fileobj(bio, MINIO_BUCKET, 'reference_data.pkl')
        
        return reference_data

def predict_batch(data):
    """Dự đoán cho một batch dữ liệu"""
    url = f"{KSERVE_ENDPOINT}/v2/models/{MODEL_NAME}/infer"
    headers = {"Content-Type": "application/json"}
    
    results = []
    
    for _, row in data.iterrows():
        # Chuyển đổi data thành định dạng KServe input
        inputs = []
        for column in data.columns:
            inputs.append({
                "name": column,
                "shape": [1],
                "datatype": "FP64",
                "data": [float(row[column])]
            })
        
        payload = {"inputs": inputs}
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response_data = response.json()
            
            # Lấy giá trị dự đoán
            prediction_value = response_data["outputs"][0]["data"][0]
            results.append(prediction_value)
        except Exception as e:
            print(f"Lỗi khi dự đoán: {str(e)}")
            results.append(None)
    
    return results

def calculate_psi(expected, actual, buckets=10):
    """Tính Population Stability Index"""
    def psi_bucket(e_perc, a_perc):
        """PSI per bucket"""
        if e_perc == 0:
            e_perc = 0.0001
        if a_perc == 0:
            a_perc = 0.0001
        return (e_perc - a_perc) * np.log(e_perc / a_perc)
    
    # Chuyển đổi thành mảng numpy
    expected = np.array(expected)
    actual = np.array(actual)
    
    # Xác định buckets trên dữ liệu expected
    breakpoints = np.arange(0, 101, 100 / buckets)
    breakpoints = np.percentile(expected, breakpoints)
    
    # Xóa các điểm trùng nhau
    breakpoints = np.unique(breakpoints)
    
    # Đếm số lượng giá trị trong mỗi bucket
    expected_counts = np.histogram(expected, bins=breakpoints)[0]
    actual_counts = np.histogram(actual, bins=breakpoints)[0]
    
    # Tính phần trăm
    expected_percents = expected_counts / len(expected)
    actual_percents = actual_counts / len(actual)
    
    # Tính PSI cho mỗi bucket và tổng
    psi_values = np.sum([psi_bucket(expected_percents[i], actual_percents[i]) 
                          for i in range(len(expected_percents))])
    
    return psi_values

def detect_data_drift():
    """Phát hiện data drift và model drift"""
    print(f"[{datetime.now()}] Bắt đầu phát hiện drift...")
    
    # Lấy dữ liệu tham chiếu
    reference_data = get_reference_data()
    
    # Tạo dữ liệu hiện tại
    current_data = generate_data(CURRENT_DATA_SIZE)
    
    # Thực hiện dự đoán
    reference_predictions = predict_batch(reference_data)
    current_predictions = predict_batch(current_data)
    
    # Loại bỏ các giá trị None
    reference_predictions = [p for p in reference_predictions if p is not None]
    current_predictions = [p for p in current_predictions if p is not None]
    
    # Tính các metric drift
    drift_metrics = {
        "timestamp": time.time(),
        "reference_data_size": len(reference_data),
        "current_data_size": len(current_data),
        "reference_predictions_size": len(reference_predictions),
        "current_predictions_size": len(current_predictions),
    }
    
    # Thêm thông tin về phân phối dự đoán
    if reference_predictions and current_predictions:
        reference_positive_rate = sum(1 for p in reference_predictions if p == 1) / len(reference_predictions)
        current_positive_rate = sum(1 for p in current_predictions if p == 1) / len(current_predictions)
        
        drift_metrics.update({
            "reference_positive_rate": reference_positive_rate * 100,
            "current_positive_rate": current_positive_rate * 100,
            "positive_rate_diff": abs(reference_positive_rate - current_positive_rate) * 100,
        })
    
    # Phát hiện input drift cho các tính năng số
    for column in reference_data.columns:
        # Kolmogorov-Smirnov test
        ks_statistic, ks_pvalue = ks_2samp(reference_data[column], current_data[column])
        
        # Population Stability Index
        psi_value = calculate_psi(reference_data[column], current_data[column])
        
        drift_detected = ks_statistic > KS_THRESHOLD or psi_value > PSI_THRESHOLD
        
        drift_metrics.update({
            f"{column}_ks_statistic": ks_statistic,
            f"{column}_ks_pvalue": ks_pvalue,
            f"{column}_psi": psi_value,
            f"{column}_drift_detected": 1 if drift_detected else 0,
        })
    
    # Log kết quả vào MLflow
    with mlflow.start_run():
        for key, value in drift_metrics.items():
            mlflow.log_metric(key, value)
        
        # Log một số thông tin về model
        mlflow.log_param("model_name", MODEL_NAME)
        mlflow.log_param("endpoint", KSERVE_ENDPOINT)
        mlflow.log_param("drift_detection_time", datetime.now().isoformat())
        
        # Log các ngưỡng sử dụng
        mlflow.log_param("psi_threshold", PSI_THRESHOLD)
        mlflow.log_param("ks_threshold", KS_THRESHOLD)
    
    # Hiển thị kết quả
    print(f"[{datetime.now()}] Đã hoàn thành phát hiện drift.")
    print(f"Tỷ lệ dự đoán dương tính (tham chiếu): {drift_metrics.get('reference_positive_rate', 'N/A'):.2f}%")
    print(f"Tỷ lệ dự đoán dương tính (hiện tại): {drift_metrics.get('current_positive_rate', 'N/A'):.2f}%")
    print(f"Chênh lệch: {drift_metrics.get('positive_rate_diff', 'N/A'):.2f}%")
    
    # Hiển thị các tính năng bị phát hiện drift
    drift_features = [col.replace("_drift_detected", "") for col, val in drift_metrics.items() 
                      if "_drift_detected" in col and val == 1]
    
    if drift_features:
        print(f"Phát hiện drift ở các tính năng: {', '.join(drift_features)}")
    else:
        print("Không phát hiện drift ở bất kỳ tính năng nào.")

def start_scheduler():
    """Bắt đầu lịch trình phát hiện drift định kỳ"""
    schedule.every(DRIFT_DETECTION_INTERVAL_HOURS).hours.do(detect_data_drift)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    print(f"[{datetime.now()}] Bắt đầu chương trình phát hiện drift...")
    
    # Cấu hình MLflow
    configure_mlflow()
    
    # Chạy phát hiện drift lần đầu
    detect_data_drift()
    
    # Bắt đầu lịch trình phát hiện drift định kỳ
    print(f"Đã lên lịch phát hiện drift mỗi {DRIFT_DETECTION_INTERVAL_HOURS} giờ.")
    
    try:
        # Bắt đầu scheduler trong một thread riêng
        scheduler_thread = threading.Thread(target=start_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        # Giữ chương trình chạy
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("Đã nhận lệnh dừng. Kết thúc chương trình.")

if __name__ == "__main__":
    main() 