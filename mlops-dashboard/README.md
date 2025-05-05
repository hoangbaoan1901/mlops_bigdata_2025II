# MLOps Dashboard

Ứng dụng dashboard để quản lý và giám sát các thành phần MLOps bao gồm MLflow, Kubeflow Pipelines và KServe.

## Tổng quan

MLOps Dashboard là một ứng dụng web giúp quản lý toàn bộ quy trình làm việc MLOps, từ khâu thử nghiệm với MLflow, triển khai pipeline với Kubeflow, đến việc triển khai và giám sát mô hình với KServe.

## Cấu trúc dự án

```
mlops-dashboard/
├── backend/           # API và backend logic
│   ├── app/           # Mã nguồn backend
│   │   ├── models/    # Pydantic data models
│   │   ├── routes/    # Định nghĩa API endpoints
│   │   ├── services/  # Business logic
│   │   └── utils/     # Hàm tiện ích
│   ├── main.py        # Entry point
│   └── requirements.txt
│
└── frontend/          # React frontend
    ├── public/        # Static files
    └── src/           # Mã nguồn frontend
        ├── components/# React components
        ├── pages/     # React pages
        ├── services/  # API services
        └── context/   # React contexts
```

## Tính năng

- **Dashboard**: Tổng quan về các thành phần MLOps
- **MLflow**: 
  - Quản lý và giám sát MLflow server
  - Hiển thị thử nghiệm và kết quả
  - Quản lý Model Registry
- **Kubeflow Pipelines**:
  - Hiển thị và quản lý các pipeline
  - Theo dõi việc chạy pipeline
  - Visualize pipeline graphs
- **KServe**:
  - Triển khai mô hình từ MLflow Model Registry
  - Quản lý việc triển khai (deployment)
  - Giám sát các endpoint triển khai

## Cài đặt và Chạy

### Backend

1. Di chuyển vào thư mục backend:
```bash
cd mlops-dashboard/backend
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Khởi động server:
```bash
python main.py
```

Backend API sẽ chạy tại: http://localhost:8000

### Frontend

1. Di chuyển vào thư mục frontend:
```bash
cd mlops-dashboard/frontend
```

2. Cài đặt các package:
```bash
npm install
```

3. Khởi động ứng dụng:
```bash
npm start
```

Frontend sẽ chạy tại: http://localhost:3000

## API Documentation

Khi backend đang chạy, bạn có thể truy cập vào tài liệu API tại:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Các API endpoint chính

### MLflow Endpoints
- `GET /mlflow/status` - Lấy trạng thái của MLflow server
- `POST /mlflow/start` - Khởi động MLflow server
- `POST /mlflow/stop` - Dừng MLflow server
- `GET /mlflow/logs` - Lấy logs của MLflow server

### Kubeflow Endpoints
- `GET /kubeflow/port-forward-command` - Lấy lệnh port-forward cho Kubeflow
- `GET /kubeflow/check-connection` - Kiểm tra kết nối Kubeflow

### KServe Endpoints
- `GET /kserve/deployments` - Danh sách các deployment
- `GET /kserve/deployments/{name}` - Lấy thông tin của một deployment
- `POST /kserve/deployments` - Tạo một deployment mới
- `DELETE /kserve/deployments/{name}` - Xóa một deployment
- `GET /kserve/deployments/{name}/logs` - Lấy logs của deployment
- `GET /kserve/serving-runtimes` - Danh sách serving runtimes
- `GET /kserve/deployments/{name}/pods` - Lấy danh sách pods của một deployment
- `GET /kserve/pods` - Lấy tất cả pods trong một namespace

## Chế độ Mock Data

Ứng dụng hỗ trợ chế độ mock data cho phát triển và thử nghiệm. Sử dụng các endpoint:
- `GET /mlflow/mock/*` - Mock data cho MLflow
- `GET /kubeflow/mock/*` - Mock data cho Kubeflow
- `GET /kserve/mock/*` - Mock data cho KServe

## Yêu cầu hệ thống

- Python 3.8+
- Node.js 14+
- Kubernetes cluster (cho KServe)
- MLflow 2.0+
- Kubeflow Pipelines 