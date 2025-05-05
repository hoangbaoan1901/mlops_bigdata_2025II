# MLOps Dashboard

Ứng dụng web để quản lý và hiển thị giao diện của MLflow và Kubeflow Pipelines.

## Tính năng

- **Dashboard tổng quan**: Thông tin và biểu đồ về ML experiments và pipeline runs
- **MLflow Management**: Bật/tắt MLflow server, xem experiments, runs, models và logs
- **Kubeflow Pipelines**: Kết nối và quản lý Kubeflow Pipelines, xem pipelines, runs và visualization
- **Chế độ xem trước UI**: Khả năng xem trước UI mà không cần kết nối với các dịch vụ thực tế

## Công nghệ sử dụng

### Backend
- FastAPI: Web framework
- MLflow: ML lifecycle platform 
- Kubeflow Pipelines: ML pipeline platform
- Websockets: Realtime logs

### Frontend
- ReactJS: UI framework
- Material-UI: UI component library
- ReactFlow: Pipeline visualization
- ChartJS: Data visualization

## Cài đặt

### Yêu cầu
- Python 3.8+
- Node.js 14+
- npm 6+
- MLflow 2.10.2+
- Kubeflow (optional)

### Bước 1: Cài đặt và chạy Backend

```bash
# Clone repository
cd mlops-dashboard/backend

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Bước 2: Cài đặt và chạy Frontend

```bash
# Đi đến thư mục frontend
cd mlops-dashboard/frontend

# Cài đặt dependencies
npm install

# Chạy ứng dụng
npm start
```

Sau khi chạy các lệnh trên, bạn có thể truy cập:
- Frontend tại: http://localhost:3000
- Backend API tại: http://localhost:8000
- API docs tại: http://localhost:8000/docs

## Hướng dẫn sử dụng

### Dashboard

Trang tổng quan hiển thị thông tin về:
- Số lượng experiments và runs trong MLflow
- Số lượng pipelines trong Kubeflow
- Biểu đồ phân tích runs và trạng thái
- Hoạt động gần đây

### MLflow

- Bật/tắt MLflow server với các tùy chọn cấu hình
- Xem danh sách experiments, runs và models
- Theo dõi logs của MLflow server
- Truy cập MLflow UI

### Kubeflow Pipelines

- Kết nối tới Kubeflow thông qua port-forward
- Xem danh sách pipelines và runs
- Visualization pipeline dưới dạng đồ thị
- Thông tin về Kubeflow Pipelines

## Môi trường

Bạn có thể cấu hình các biến môi trường cho backend trong file `.env`:

```
API_PORT=8000
MLFLOW_DEFAULT_PORT=5000
MLFLOW_DEFAULT_HOST=0.0.0.0
MLFLOW_DEFAULT_ARTIFACT_URI=./mlruns
KUBEFLOW_DEFAULT_PORT=8080
KUBEFLOW_DEFAULT_NAMESPACE=kubeflow
KUBEFLOW_DEFAULT_SERVICE=ml-pipeline-ui
CORS_ORIGINS=http://localhost:3000
```

## Lưu ý

- Khi sử dụng Kubeflow Pipelines, bạn cần có quyền truy cập đến một Kubernetes cluster có Kubeflow đã được cài đặt
- Để sử dụng tính năng port-forward cho Kubeflow, bạn cần cài đặt và cấu hình kubectl

## License

MIT License 