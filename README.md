# MLOps Pipeline với Kubeflow, MLflow và Feast

Dự án này là một ví dụ về việc xây dựng và triển khai MLOps pipeline end-to-end, tích hợp các công cụ MLOps hiện đại như Kubeflow, MLflow và Feast. Dự án bao gồm hai bài toán minh họa: dự đoán khách hàng rời bỏ ngân hàng (Bank Churn Prediction) và dự đoán giá cổ phiếu (Stock Price Prediction).

## Tổng Quan

### Mục Tiêu
- Xây dựng một MLOps pipeline hoàn chỉnh có thể tái sử dụng cho nhiều dự án ML
- Minh họa việc tích hợp các công cụ MLOps phổ biến trong hệ sinh thái Big Data
- Demo quy trình ML end-to-end từ data preparation đến model deployment và monitoring

### Use Cases
1. **Bank Churn Prediction**:
   - Dữ liệu: Thông tin khách hàng (độ tuổi, điểm tín dụng, số sản phẩm, v.v.)
   - Mục tiêu: Dự đoán khách hàng có rời bỏ ngân hàng hay không
   - Nguồn dữ liệu: MinIO storage (s3://mlflow/churn.csv)

2. **Stock Price Prediction**:
   - Dữ liệu: Thông tin giá cổ phiếu theo thời gian thực
   - Mục tiêu: Dự đoán giá cổ phiếu trong tương lai
   - Xử lý: Sử dụng Spark để xử lý dữ liệu lớn, Kafka để xử lý luồng dữ liệu thời gian thực

## Kiến Trúc MLOps

Hệ thống tích hợp các thành phần MLOps hiện đại:

### 1. **Kubeflow**
- **Mô tả**: Nền tảng ML orchestration trên Kubernetes
- **Chức năng chính**:
  - Orchestration và automation cho ML workflows
  - Pipeline definitions và executions
  - Component composition và reuse
  - Resource management cho training jobs
- **Cách tích hợp trong dự án**: Định nghĩa các ML pipeline components, scheduling và monitoring các jobs

### 2. **MLflow**
- **Mô tả**: Framework mã nguồn mở cho ML lifecycle
- **Chức năng chính**:
  - Experiment tracking: Ghi lại parameters, metrics, artifacts
  - Model registry: Quản lý và version control models
  - Model serving: Triển khai models thành REST API endpoints
- **Cách tích hợp trong dự án**: Tracking experiments, lưu trữ và đăng ký models, triển khai models thành services

### 3. **Feast**
- **Mô tả**: Feature store cho ML
- **Chức năng chính**:
  - Feature definitions và transformations
  - Point-in-time feature retrieval
  - Feature serving cho online và offline use cases
  - Feature consistency giữa training và inference
- **Cách tích hợp trong dự án**: Quản lý features cho cả Bank Churn và Stock Price models

### 4. **MinIO**
- **Mô tả**: High-performance object storage
- **Chức năng chính**:
  - S3-compatible storage cho datasets và model artifacts
  - Data versioning
  - Access control và security
- **Cách tích hợp trong dự án**: Lưu trữ datasets, features và model artifacts

### 5. **Apache Spark**
- **Mô tả**: Unified analytics engine cho Big Data
- **Chức năng chính**:
  - Distributed data processing
  - Batch và streaming processing
  - ML capabilities (Spark MLlib)
- **Cách tích hợp trong dự án**: Xử lý dữ liệu lớn cho Stock Price prediction, feature transformations

### 6. **Apache Kafka**
- **Mô tả**: Distributed streaming platform
- **Chức năng chính**:
  - Real-time data streaming
  - Event sourcing
  - Scalable message processing
- **Cách tích hợp trong dự án**: Thu thập dữ liệu real-time cho Stock Price use case

### 7. **KServe**
- **Mô tả**: Serverless inferencing platform trên Kubernetes
- **Chức năng chính**:
  - Model serving với auto-scaling
  - Canary deployment và A/B testing
  - Multi-framework (TensorFlow, PyTorch, scikit-learn, XGBoost)
  - Inference request logging và explainability
- **Cách tích hợp trong dự án**: Triển khai production models với khả năng auto-scaling và monitoring

## Cấu Trúc Project
```
mlops_bigdata_2025II/
├── bank_churn_test/                # Bank Churn Prediction use case
│   ├── dataset/                    # Dataset cho Bank Churn
│   ├── pipeline/                   # Kubeflow pipeline definitions
│   ├── deploy/                     # Deployment configurations
│   └── monitoring/                 # Model monitoring
├── stock_price_test/               # Stock Price Prediction use case
│   ├── DataProcessors.py           # Data processing utilities
│   ├── RegressionModel.py          # ML model implementations
│   ├── kafka_producer.py           # Kafka producer cho real-time data
│   ├── spark-consumer.py           # Spark streaming consumer
│   ├── spark-batch-processor.py    # Spark batch processing
│   ├── read_delta_table.py         # Delta Lake integration
│   ├── kubeflow_components/        # Kubeflow component definitions
│   └── spark-submit.sh             # Script để submit Spark jobs
├── spark_setup/                    # Spark installation và configuration
│   └── spark-values.yaml           # Helm values cho Spark
├── requirements.txt                # Project dependencies
└── README.md                       # Main project documentation
```

## Chi Tiết Về MLOps Pipeline Components

### 1. **Data Ingestion & Storage**
- **Công nghệ sử dụng**: 
  - MinIO (S3-compatible storage)
  - Kafka (real-time data)
  - Delta Lake (data versioning)
- **Quy trình**:
  - Bank Churn: Import CSV data vào MinIO
  - Stock Price: Stream real-time data thông qua Kafka
- **Artifacts**: Raw datasets, data schema definitions

### 2. **Data Processing & Feature Engineering**
- **Công nghệ sử dụng**:
  - Apache Spark cho distributed processing
  - Feast cho feature store
- **Quy trình**:
  - Data cleaning & validation
  - Feature transformations & engineering
  - Feature registration với Feast
- **Artifacts**: Processed datasets, feature definitions, transformation pipelines

### 3. **Model Training & Evaluation**
- **Công nghệ sử dụng**:
  - Kubeflow Pipelines cho orchestration
  - MLflow cho experiment tracking
  - Spark MLlib cho distributed training
- **Quy trình**:
  - Hyperparameter tuning
  - Cross-validation
  - Model selection
  - Metrics logging
- **Artifacts**: Trained models, evaluation metrics, experiment logs

### 4. **Model Registry & Versioning**
- **Công nghệ sử dụng**:
  - MLflow Model Registry
  - Git cho code versioning
- **Quy trình**:
  - Model registration
  - Version tagging (staging, production)
  - Model lineage tracking
- **Artifacts**: Versioned models, model metadata

### 5. **Model Deployment & Serving**
- **Công nghệ sử dụng**:
  - KServe cho model inference
  - MLflow Model Registry cho model versioning
  - Feast Serving cho feature serving
- **Quy trình**:
  - Model packaging theo chuẩn KServe
  - Service deployment với canary và traffic splitting
  - Integration với feature store
  - API documentation cho consumers
- **Artifacts**: InferenceService manifests, API documentation, model transformers

### 6. **Model Monitoring & Feedback Loop**
- **Công nghệ sử dụng**:
  - Prometheus cho metrics collection
  - Grafana cho visualization
- **Quy trình**:
  - Real-time performance monitoring
  - Concept drift detection
  - Automated retraining triggers
- **Artifacts**: Monitoring dashboards, alerting rules

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

### Kafka Configuration
```yaml
bootstrap.servers: kafka:9092
topic: stock-prices
```

### Spark Configuration
Xem chi tiết trong `spark_setup/spark-values.yaml`

## Hướng Dẫn Cài Đặt Các Thành Phần

### 1. Cài Đặt Python Environment
```bash
# Tạo Python virtual environment
python -m venv mlops-venv
source mlops-venv/bin/activate  # Linux/Mac
# hoặc
# mlops-venv\Scripts\activate  # Windows

# Cài đặt các thư viện cần thiết với phiên bản cụ thể
pip install -r requirements.txt

# Nếu cần cài đặt thủ công, đảm bảo sử dụng các phiên bản tương thích
pip install tensorflow==2.10.0
pip install scikit-learn==1.1.3
pip install mlflow==2.4.1
pip install kfp==1.8.22
pip install feast==0.30.1
pip install pyspark==3.3.2
pip install kafka-python==2.0.2
pip install delta-spark==2.3.0
pip install minio==7.1.14
pip install prometheus-client==0.16.0
```

### 2. Cài Đặt Kubernetes
```bash
# Cài đặt kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Cài đặt K3d (Kubernetes trong Docker) cho development
curl -s https://raw.githubusercontent.com/rancher/k3d/main/install.sh | bash

# Tạo cluster
k3d cluster create mlops-cluster --api-port 6550 -p "8080:80@loadbalancer"
```

### 2. Cài Đặt Kubeflow
```bash
# Clone Kubeflow manifests 
git clone https://github.com/kubeflow/manifests.git

# Sử dụng kustomize để cài đặt
cd manifests
while ! kustomize build example | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done

# Kiểm tra trạng thái
kubectl get pods -n kubeflow
```

### 3. Cài Đặt MinIO
```bash
# Sử dụng Helm để cài đặt MinIO
helm repo add minio https://charts.min.io/
helm repo update
helm install minio minio/minio --namespace kubeflow --create-namespace \
  --set accessKey=minio,secretKey=minio123,persistence.size=10Gi

# Port forwarding cho MinIO UI
kubectl port-forward -n kubeflow svc/minio 9000:9000
```

### 4. Cài Đặt MLflow
```bash
# Sử dụng Helm để cài đặt MLflow
helm repo add community-charts https://community-charts.github.io/helm-charts
helm repo update
helm install mlflow community-charts/mlflow \
  --namespace kubeflow \
  --set backendStore.databaseConnectionString="sqlite:///mlflow.db" \
  --set artifactRoot.s3.enabled=true \
  --set artifactRoot.s3.bucket=mlflow \
  --set artifactRoot.s3.endpoint=http://minio-service.kubeflow:9000 \
  --set artifactRoot.s3.accessKey=minio \
  --set artifactRoot.s3.secretKey=minio123

# Port forwarding cho MLflow UI
kubectl port-forward -n kubeflow svc/mlflow-server-service 5000:5000
```

### 5. Cài Đặt Feast
```bash
# Cài đặt Feast qua pip
pip install feast

# Tạo project Feast
feast init feature_repo
cd feature_repo

# Cấu hình registry để lưu trữ feature definitions
# Chỉnh sửa feature_store.yaml
```

#### Cấu Hình Feast Feature Store
Tạo file `feature_store.yaml` với nội dung như sau:

```yaml
project: bank_churn_project
registry: 
  registry_type: sql
  path: sqlite:///registry.db
provider: local
online_store:
  type: redis
  connection_string: localhost:6379
offline_store:
  type: file
entity_key_serialization_version: 2
```

Tạo file `features.py` để định nghĩa features:

```python
from datetime import datetime, timedelta
from feast import Entity, Feature, FeatureView, FileSource, ValueType

# Định nghĩa entities
customer = Entity(
    name="customer_id", 
    description="customer identifier",
    value_type=ValueType.INT64
)

# Định nghĩa data source
customer_data_source = FileSource(
    path="data/customer_features.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# Định nghĩa feature view
customer_features = FeatureView(
    name="customer_features",
    entities=["customer_id"],
    ttl=timedelta(days=90),
    features=[
        Feature(name="age", dtype=ValueType.INT64),
        Feature(name="balance", dtype=ValueType.FLOAT),
        Feature(name="credit_score", dtype=ValueType.INT64),
        Feature(name="num_products", dtype=ValueType.INT64),
        Feature(name="is_active", dtype=ValueType.BOOL),
    ],
    batch_source=customer_data_source,
)
```

Sau khi định nghĩa features, apply changes vào feature store:

```bash
feast apply
```

### 6. Cài Đặt Apache Spark
```bash
# Cài đặt Spark trên Kubernetes
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install spark bitnami/spark -f spark_setup/spark-values.yaml -n spark-system --create-namespace

# Kiểm tra trạng thái
kubectl get pods -n spark-system
```

### 7. Cài Đặt Apache Kafka
```bash
# Cài đặt Kafka trên Kubernetes 
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install kafka bitnami/kafka \
  --namespace kafka-system --create-namespace \
  --set replicaCount=3 \
  --set externalAccess.enabled=true \
  --set externalAccess.service.type=NodePort

# Kiểm tra trạng thái
kubectl get pods -n kafka-system
```

### 8. Cài Đặt Monitoring Tools
```bash
# Cài đặt Prometheus và Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Port forwarding cho Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

### 9. Cấu Hình Network Connectivity
```bash
# Tạo NetworkPolicy cho giao tiếp giữa các namespace
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
  namespace: kubeflow
spec:
  podSelector: {}
  ingress:
  - {}
  policyTypes:
  - Ingress
EOF
```

## Hướng Dẫn Thiết Lập & Sử Dụng

### 1. Setup Infrastructure
```bash
# Clone repository
git clone <repository_url> mlops_bigdata_2025II
cd mlops_bigdata_2025II

# Cài đặt dependencies
pip install -r requirements.txt

# Kiểm tra kết nối services
kubectl get pods -n kubeflow
```

### 2. Bank Churn Pipeline
```bash
cd bank_churn_test/pipeline
python kubeflow_pipeline_basic.py
```

### 3. Stock Price Pipeline
```bash
# Khởi động Kafka producer để simulate real-time data
cd stock_price_test
python kafka_producer.py

# Chạy Spark batch processor
./spark-submit.sh spark-batch-processor.py

# Chạy Spark streaming consumer
./spark-submit.sh spark-consumer.py
```

### 4. Truy Cập Dashboards
- Kubeflow Dashboard: http://localhost:8080
- MLflow UI: http://localhost:5000
- Grafana Monitoring: http://localhost:3000

## Best Practices & Lưu Ý

### 1. Data Management
- Sử dụng MinIO và Delta Lake cho data versioning
- Tracking data lineage với Feast
- Đảm bảo reproducibility bằng data immutability

### 2. Experiment Management
- Log tất cả experiments, parameters và metrics với MLflow
- Version control cho cả code và data
- Document experiment configurations và results

### 3. Model Management
- Implement CI/CD cho model deployment
- Automated A/B testing
- Rollback capabilities

### 4. Resource Optimization
- GPU/CPU allocation trên Kubernetes
- Distributed training với Spark
- Resource quotas và limits

## Xử Lý Sự Cố

Kiểm tra các điểm sau nếu gặp vấn đề:
1. Kết nối services (Kubeflow, MinIO, MLflow, Kafka, Spark)
2. Permissions và credentials (đặc biệt là cho MinIO và Kafka)
3. Resource limits trong Kubernetes
4. Pipeline logs trong Kubeflow UI
5. Network connectivity giữa các services

## Đóng Góp & Phát Triển

Dự án này là một template MLOps có thể được tùy chỉnh và mở rộng. Các hướng phát triển:
1. Thêm automated testing và CI/CD pipelines
2. Tích hợp thêm công cụ như Seldon Core cho ML serving
3. Bổ sung công cụ monitoring như Prometheus và Grafana
4. Thêm các use cases mới và datasets khác
5. Cải thiện security và scalability

## Liên Hệ & Hỗ Trợ

Nếu bạn gặp vấn đề hoặc muốn đóng góp, vui lòng:
- Tạo issue trong repository
- Liên hệ team phát triển
- Đóng góp pull requests 