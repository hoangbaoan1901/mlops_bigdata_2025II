import kfp
from kfp import dsl
from kubernetes import client, config
from kubernetes.client.models import V1Volume, V1VolumeMount, V1HostPathVolumeSource


@dsl.component(
    base_image="python:3.9",
    packages_to_install=[
        "pandas==2.1.4",
        "scikit-learn==1.3.2",
        "boto3==1.34.0"
    ]
)
def preprocess_data(
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str
) -> dict:
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    import boto3
    from botocore.client import Config
    import pickle
    from io import BytesIO
    
    # Khởi tạo MinIO client
    s3_client = boto3.client(
        's3',
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # Đọc dữ liệu từ MinIO
    try:
        response = s3_client.get_object(Bucket=minio_bucket, Key='churn.csv')
        data = pd.read_csv(response['Body'])
    except Exception as e:
        raise Exception(f"Không thể đọc dữ liệu từ MinIO: {str(e)}")
    
    # Preprocessing
    data = data.drop(['RowNumber', 'CustomerId', 'Surname'], axis=1)
    
    # Encode categorical variables
    le = LabelEncoder()
    data['Geography'] = le.fit_transform(data['Geography'])
    data['Gender'] = le.fit_transform(data['Gender'])
    
    # Prepare features and target
    y = data['Exited']
    X = data.drop('Exited', axis=1)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    
    # Lưu dữ liệu đã xử lý vào MinIO
    train_data = {
        'X_train': X_train,
        'y_train': y_train,
        'X_test': X_test,
        'y_test': y_test,
        'feature_names': X.columns.tolist()
    }
    
    # Serialize data
    with BytesIO() as bio:
        pickle.dump(train_data, bio)
        bio.seek(0)
        s3_client.upload_fileobj(bio, minio_bucket, 'processed_data.pkl')
    
    return {
        'feature_names': X.columns.tolist(),
        'data_path': f's3://{minio_bucket}/processed_data.pkl'
    }

@dsl.component(
    base_image="python:3.9",
    packages_to_install=[
        "pandas==2.1.4",
        "scikit-learn==1.3.2",
        "boto3==1.34.0",
        "mlflow==2.10.2",
        "numpy==1.26.4"
    ]
)
def train_model(
    preprocessed_data: dict,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str,
    mlflow_tracking_uri: str = "http://mlflow.kubeflow.svc.cluster.local:5000"
) -> dict:
    import pickle
    from sklearn.linear_model import LogisticRegression
    import boto3
    from botocore.client import Config
    from io import BytesIO
    import os
    import mlflow
    import mlflow.sklearn
    import numpy as np
    import pandas as pd
    from mlflow.models.signature import infer_signature
    
    # Configure MinIO for MLflow
    os.environ["AWS_ACCESS_KEY_ID"] = minio_access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = minio_secret_key
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = minio_endpoint
    
    # Khởi tạo MinIO client
    s3_client = boto3.client(
        's3',
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # Đọc dữ liệu đã xử lý
    bucket = preprocessed_data['data_path'].split('/')[2]
    key = preprocessed_data['data_path'].split('/')[3]
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    train_data = pickle.loads(response['Body'].read())
    
    # Create a DataFrame for the features (helps with JSON compatibility)
    feature_names = preprocessed_data['feature_names']
    X_train_df = pd.DataFrame(train_data['X_train'], columns=feature_names)
    
    # Train model
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_df, train_data['y_train'])
    
    # Create a sample input for inference
    sample_input = X_train_df.iloc[:1]
    
    # Infer the model signature from inputs
    # This helps MLServer understand the expected input format
    predictions = model.predict(X_train_df)
    signature = infer_signature(X_train_df, predictions)
    
    # Set up MLflow
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("bank-churn-prediction2")
    
    # Log model with MLflow
    with mlflow.start_run() as run:
        mlflow.log_params({
            'max_iter': 1000,
            'solver': 'lbfgs'
        })
        
        # Log the model using MLflow with signature and input example
        mlflow.sklearn.log_model(
            model, 
            "model",
            signature=signature,
            input_example=sample_input,
            pip_requirements=[
                "scikit-learn==1.3.2",
                "pandas==2.1.4",
                "numpy==1.26.4"
            ]
        )
        model_uri = f"runs:/{run.info.run_id}/model"
        
        # Save model to MinIO as well (for compatibility with evaluate_model)
        with BytesIO() as bio:
            pickle.dump(model, bio)
            bio.seek(0)
            s3_client.upload_fileobj(bio, minio_bucket, 'model.pkl')
            
        # Also save the schema information for reference
        schema_info = {
            "feature_names": feature_names,
            "sample_input_json": sample_input.to_dict(orient="split"),
            "signature": str(signature)
        }
        
        mlflow.log_dict(schema_info, "model_schema.json")
    
    return {
        'model_path': f's3://{minio_bucket}/model.pkl',
        'mlflow_model_uri': model_uri,
        'mlflow_run_id': run.info.run_id,
        'feature_names': preprocessed_data['feature_names'],
        'model_params': {
            'max_iter': 1000,
            'solver': 'lbfgs'
        }
    }

@dsl.component(
    base_image="python:3.9",
    packages_to_install=[
        "pandas==2.1.4",
        "scikit-learn==1.3.2",
        "boto3==1.34.0"
    ]
)
def evaluate_model(
    model_info: dict,
    preprocessed_data: dict,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str
) -> dict:
    import pickle
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    import boto3
    from botocore.client import Config
    from io import BytesIO
    import numpy as np
    
    # Khởi tạo MinIO client
    s3_client = boto3.client(
        's3',
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # Đọc model
    bucket = model_info['model_path'].split('/')[2]
    key = model_info['model_path'].split('/')[3]
    response = s3_client.get_object(Bucket=bucket, Key=key)
    model = pickle.loads(response['Body'].read())
    
    # Đọc dữ liệu test
    bucket = preprocessed_data['data_path'].split('/')[2]
    key = preprocessed_data['data_path'].split('/')[3]
    response = s3_client.get_object(Bucket=bucket, Key=key)
    test_data = pickle.loads(response['Body'].read())
    
    # Make predictions
    y_pred = model.predict(test_data['X_test'])
    
    # Calculate metrics
    metrics = {
        'accuracy': float(accuracy_score(test_data['y_test'], y_pred)),
        'precision': float(precision_score(test_data['y_test'], y_pred)),
        'recall': float(recall_score(test_data['y_test'], y_pred)),
        'f1': float(f1_score(test_data['y_test'], y_pred))
    }
    
    # Get feature importance
    feature_importance = dict(zip(
        model_info['feature_names'],
        model.coef_[0].tolist()
    ))
    
    return {
        'metrics': metrics,
        'feature_importance': feature_importance,
        'model_params': model_info['model_params']
    }

@dsl.component(
    base_image="python:3.9",
    packages_to_install=[
        "mlflow==2.10.2",
        "boto3==1.34.0"
    ]
)
def log_to_mlflow(
    results: dict,
    mlflow_tracking_uri: str,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str
) -> None:
    import mlflow
    import os
    
    # Configure MinIO for MLflow
    os.environ["AWS_ACCESS_KEY_ID"] = minio_access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = minio_secret_key
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = minio_endpoint

    # Set MLflow tracking URI
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("bank-churn-prediction2")

    # Log to MLflow
    with mlflow.start_run():
        # Log parameters
        for param_name, param_value in results["model_params"].items():
            mlflow.log_param(param_name, param_value)
        
        # Log metrics
        for metric_name, metric_value in results["metrics"].items():
            mlflow.log_metric(metric_name, metric_value)
        
        # Log feature importance
        mlflow.log_dict(results["feature_importance"], "feature_importance.json")

@dsl.pipeline(
    name="Bank Churn Prediction Pipeline",
    description="Predicts customer churn using Logistic Regression with MinIO storage"
)
def churn_pipeline():
    # MinIO configuration
    minio_endpoint = "http://minio-service.kubeflow.svc.cluster.local:9000"
    minio_access_key = "minio"
    minio_secret_key = "minio123"
    minio_bucket = "mlflow-artifacts"
    
    # Preprocess data
    preprocess = preprocess_data(
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket=minio_bucket
    )
    
    # Train model
    train = train_model(
        preprocessed_data=preprocess.output,
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket=minio_bucket
    )
    
    # Evaluate model
    evaluate = evaluate_model(
        model_info=train.output,
        preprocessed_data=preprocess.output,
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket=minio_bucket
    )
    
    # Log to MLflow
    log_mlflow = log_to_mlflow(
        results=evaluate.output,
        mlflow_tracking_uri="http://mlflow.kubeflow.svc.cluster.local:5000",
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket=minio_bucket
    )
    
    # Set dependencies
    train.after(preprocess)
    evaluate.after(train)
    log_mlflow.after(evaluate)

if __name__ == "__main__":
    client = kfp.Client(host="http://localhost:8080")
    client.create_run_from_pipeline_func(
        churn_pipeline,
        arguments={},
        namespace="kubeflow"
    )