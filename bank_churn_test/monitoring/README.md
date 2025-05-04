# Bank Customer Churn Model Monitoring

This directory contains the monitoring system for the bank customer churn prediction model deployed with KServe. The monitoring system tracks model performance, system resource usage, and helps manage MLflow runs.

## Directory Structure

```
monitoring/
├── config/             # Configuration files
│   └── mlflow_config.py
├── utils/              # Utility functions
│   ├── kserve_client.py
│   ├── mlflow_utils.py
│   └── system_metrics.py
├── scripts/            # Executable scripts
│   ├── client_test.py
│   ├── dashboard.py
│   └── run_cleanup.py
├── model_monitor.py    # Main monitoring module
└── requirements.txt    # Dependencies
```

## Features

- **Model Performance Monitoring**: Track prediction distributions, response times, and success rates
- **System Resource Monitoring**: CPU, memory, and disk usage tracking
- **MLflow Integration**: Comprehensive logging of metrics with proper run management
- **Stuck Run Cleanup**: Tools to terminate stuck MLflow runs
- **Visualization**: Dashboard for visualizing monitoring metrics

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure MLflow and KServe settings in `config/mlflow_config.py`

## Usage

### Run Monitoring Service

Start the monitoring service to collect metrics at regular intervals:

```bash
python model_monitor.py
```

### Test Model Predictions

Run a test batch of predictions:

```bash
python scripts/client_test.py
```

### Generate Monitoring Dashboard

Create visualizations based on collected metrics:

```bash
python scripts/dashboard.py --experiment bank-churn-monitoring
```

### Clean Up Stuck MLflow Runs

Terminate any stuck active runs:

```bash
python scripts/run_cleanup.py --all
```

Or terminate runs for a specific experiment:

```bash
python scripts/run_cleanup.py --experiment bank-churn-monitoring
```

## Metrics Tracked

- **Prediction Metrics**: Churn rate, prediction distribution
- **Performance Metrics**: Response time, throughput, SLA violations
- **System Metrics**: CPU usage, memory usage, disk usage
- **Trend Metrics**: Changes in response time, success rate, and prediction distribution