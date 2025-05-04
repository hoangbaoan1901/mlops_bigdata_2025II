# Bank Churn Model Deployment

Hệ thống triển khai model dự đoán khách hàng rời bỏ (churn) ngân hàng bằng KServe.

## Cấu trúc dự án

```
.
├── config/                   # Cấu hình dự án
│   └── mlflow_config.py      # Cấu hình MLflow và MinIO
├── utils/                    # Các tiện ích
│   └── kserve_client.py      # Tiện ích tương tác với KServe
├── bank_churn_serve.yaml     # Cấu hình KServe InferenceService
├── service-account.yaml      # Cấu hình Service Account cho KServe
├── secret.yaml               # Cấu hình Secret cho MinIO
└── requirements.txt          # Danh sách các thư viện cần thiết
```

> **Lưu ý:** Các tính năng giám sát và monitoring đã được chuyển sang thư mục `monitoring/` riêng biệt.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Triển khai model

1. Áp dụng cấu hình Secret và Service Account:

```bash
kubectl apply -f secret.yaml -n bankchurn-kserve-2
kubectl apply -f service-account.yaml -n bankchurn-kserve-2
```

2. Triển khai model với KServe:

```bash
kubectl apply -f bank_churn_serve.yaml -n bankchurn-kserve-2
```

3. Kiểm tra trạng thái:

```bash
kubectl get inferenceservices -n bankchurn-kserve-2
kubectl get pods -n bankchurn-kserve-2
```

## Truy cập model

Để truy cập model trực tiếp từ máy local:

```bash
kubectl port-forward -n bankchurn-kserve service/bankchurn-predictor 8085:80
```

## Định dạng dữ liệu đầu vào

```json
{
  "inputs": [
    {"name": "CreditScore", "datatype": "FP64", "shape": [1], "data": [619]},
    {"name": "Geography", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "Gender", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "Age", "datatype": "FP64", "shape": [1], "data": [42]},
    {"name": "Tenure", "datatype": "FP64", "shape": [1], "data": [2]},
    {"name": "Balance", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "NumOfProducts", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "HasCrCard", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "IsActiveMember", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "EstimatedSalary", "datatype": "FP64", "shape": [1], "data": [101348.88]}
  ]
}
```

## Giám sát (Monitoring)

Tất cả chức năng giám sát đã được chuyển sang thư mục `monitoring/`. Vui lòng tham khảo README trong thư mục đó để biết thêm chi tiết về:

- Giám sát hiệu suất model
- Xử lý MLflow run bị kẹt
- Tạo báo cáo và dashboard
- Thu thập metrics hệ thống 