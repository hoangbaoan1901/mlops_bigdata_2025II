# MLOps Pipeline với Kubeflow, MLflow và Feast

Dự án này là một ví dụ về việc xây dựng và triển khai MLOps pipeline end-to-end, tích hợp các công cụ MLOps hiện đại như Kubeflow, MLflow và Feast. Để minh họa pipeline, chúng tôi sử dụng bài toán dự đoán khách hàng rời bỏ ngân hàng (Bank Churn Prediction) như một use case điển hình.

## Tổng Quan

### Mục Tiêu
- Xây dựng một MLOps pipeline hoàn chỉnh có thể tái sử dụng cho nhiều dự án ML
- Minh họa việc tích hợp các công cụ MLOps phổ biến
- Demo quy trình ML end-to-end từ data preparation đến model deployment

### Dataset Minh Họa
Dự án sử dụng dataset Bank Churn làm ví dụ, bao gồm:
- Thông tin khách hàng (độ tuổi, điểm tín dụng, số sản phẩm, v.v.)
- Label: Khách hàng có rời bỏ ngân hàng hay không
- Nguồn dữ liệu: MinIO storage (s3://mlflow/churn.csv)

## Kiến Trúc MLOps

Hệ thống tích hợp các thành phần MLOps hiện đại:
- **Kubeflow Pipelines**: Orchestration và automation cho ML workflows
- **Feast**: Feature store cho feature engineering và serving
- **MLflow**: Experiment tracking, model registry và deployment
- **MinIO**: Object storage cho data versioning và model artifacts

## Yêu Cầu Hệ Thống

### Cài Đặt Dependencies
```bash
cd mlops_bigdata_2025II
pip install -r mlflow-kubeflow/requirements.txt
```

### Yêu Cầu Cơ Sở Hạ Tầng
- Kubernetes cluster với Kubeflow đã được cài đặt
- MinIO service đang chạy và có thể truy cập
- MLflow tracking server đang chạy

## MLOps Pipeline Components

1. **Data & Feature Engineering**
   - Feature store preparation với Feast
   - Automated data validation và transformation
   - Feature versioning và tracking

2. **Model Development**
   - Experiment tracking với MLflow
   - Model versioning
   - Hyperparameter tuning
   - Model evaluation và validation

3. **Model Deployment**
   - Model serving thông qua Kubeflow
   - Feature serving với Feast
   - Monitoring và logging

## Cấu Trúc Project
```
mlops_bigdata_2025II/
├── mlflow-kubeflow/
│   ├── feature_store/
│   │   └── feature_store.yaml    # Feast configuration
│   ├── kubeflow_pipeline_feast.py # MLOps pipeline implementation
│   ├── requirements.txt          # Project dependencies
│   └── README.md                # Documentation
└── README.md                    # Main project documentation
```

## Cấu Hình

### MinIO Configuration
```yaml
endpoint: http://minio-service.kubeflow:9000
access_key: minio
secret_key: minio123
bucket: mlflow
```

### MLflow Configuration
```
tracking_uri: http://mlflow-server-service.kubeflow:5000
```

## Hướng Dẫn Sử Dụng

1. **Setup Infrastructure**
```bash
# Clone repository
git clone <repository_url> mlops_bigdata_2025II
cd mlops_bigdata_2025II

# Cài đặt dependencies
pip install -r mlflow-kubeflow/requirements.txt

# Kiểm tra kết nối services
kubectl get pods -n kubeflow
```

2. **Chạy Pipeline**
```bash
cd mlflow-kubeflow
python kubeflow_pipeline_feast.py
```

3. **Monitoring**
- Kubeflow Dashboard: http://localhost:8080
- MLflow UI: http://localhost:5000

## Best Practices & Lưu Ý

1. **Data Version Control**
   - Sử dụng MinIO để version control datasets
   - Tracking data lineage với Feast

2. **Experiment Management**
   - Log tất cả experiments với MLflow
   - Theo dõi metrics và parameters

3. **Model Management**
   - Version control cho models
   - Automated model validation
   - Model deployment tracking

## Xử Lý Sự Cố

Kiểm tra các điểm sau nếu gặp vấn đề:
1. Kết nối services (Kubeflow, MinIO, MLflow)
2. Permissions và credentials
3. Resource limits trong Kubernetes
4. Pipeline logs trong Kubeflow UI

## Đóng Góp & Phát Triển

Dự án này là một template MLOps có thể được tùy chỉnh và mở rộng. Các hướng phát triển:
1. Thêm automated testing
2. Tích hợp CI/CD
3. Bổ sung monitoring tools
4. Thêm các use cases khác

## Liên Hệ & Hỗ Trợ

Nếu bạn gặp vấn đề hoặc muốn đóng góp, vui lòng:
- Tạo issue trong repository
- Liên hệ team phát triển
- Đóng góp pull requests 