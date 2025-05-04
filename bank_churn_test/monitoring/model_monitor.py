#!/usr/bin/env python
import time
from datetime import datetime, timedelta
import threading
import schedule
import statistics
import uuid
import numpy as np
from scipy import stats
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

# Import from monitoring modules
from config.mlflow_config import configure_mlflow, ensure_no_active_runs
from utils.kserve_client import check_model_health, generate_test_data, predict_churn
from utils.system_metrics import get_system_metrics

# Global configuration
MONITORING_INTERVAL_MINUTES = 0.1
BATCH_SIZE = 10  # Số lượng dự đoán mỗi batch
MAX_RESPONSE_TIME_MS = 1000  # Thời gian phản hồi tối đa mong muốn (ms)

# Cấu hình lưu lịch sử giám sát
HISTORY_SIZE = 10  # Số lượng batch gần nhất để lưu lịch sử

# Thời gian theo dõi
TIME_WINDOW_HOURS = 24  # Cửa sổ thời gian để theo dõi xu hướng (giờ)

# Lưu trữ lịch sử monitoring
monitoring_history = {
    "timestamps": [],
    "raw_timestamps": [],  # Stores datetime objects for time series analysis
    "response_times": [],
    "success_rates": [],
    "prediction_distributions": [],
    "resource_usages": [],
    "time_metrics": {
        "hourly": {},
        "daily": {},
        "weekly": {}
    }
}

def update_monitoring_history(metrics, predictions):
    """Cập nhật lịch sử monitoring với tập trung vào các yếu tố thời gian"""
    global monitoring_history
    
    current_time = datetime.now()
    
    # Thêm thông tin mới
    monitoring_history["timestamps"].append(current_time.isoformat())
    monitoring_history["raw_timestamps"].append(current_time)
    monitoring_history["response_times"].append(metrics.get("avg_response_time", 0))
    monitoring_history["success_rates"].append(metrics.get("success_rate", 0))
    
    # Thêm phân phối dự đoán
    prediction_values = [p.get("outputs", [{}])[0].get("data", [0])[0] for p in predictions if p.get("success", False)]
    prediction_dist = {
        "0": sum(1 for v in prediction_values if v == 0) / max(1, len(prediction_values)),
        "1": sum(1 for v in prediction_values if v == 1) / max(1, len(prediction_values))
    }
    monitoring_history["prediction_distributions"].append(prediction_dist)
    
    # Thêm thông tin tài nguyên
    monitoring_history["resource_usages"].append(get_system_metrics())
    
    # Cập nhật time-based metrics
    hour_key = current_time.strftime("%Y-%m-%d-%H")
    day_key = current_time.strftime("%Y-%m-%d")
    week_key = f"{current_time.year}-{current_time.isocalendar()[1]}"
    
    # Hourly metrics
    if hour_key not in monitoring_history["time_metrics"]["hourly"]:
        monitoring_history["time_metrics"]["hourly"][hour_key] = {
            "request_count": 0,
            "success_count": 0,
            "response_times": [],
            "error_count": 0,
            "prediction_counts": {0: 0, 1: 0}
        }
    
    hourly_data = monitoring_history["time_metrics"]["hourly"][hour_key]
    hourly_data["request_count"] += len(predictions)
    hourly_data["success_count"] += sum(1 for p in predictions if p.get("success", False))
    hourly_data["error_count"] += sum(1 for p in predictions if not p.get("success", False))
    hourly_data["response_times"].extend([p.get("response_time", 0) for p in predictions if p.get("success", False)])
    
    for p in predictions:
        if p.get("success", False) and p.get("outputs"):
            pred_value = p.get("outputs", [{}])[0].get("data", [0])[0]
            hourly_data["prediction_counts"][pred_value] = hourly_data["prediction_counts"].get(pred_value, 0) + 1
    
    # Daily metrics - similar structure to hourly
    if day_key not in monitoring_history["time_metrics"]["daily"]:
        monitoring_history["time_metrics"]["daily"][day_key] = {
            "request_count": 0,
            "success_count": 0,
            "response_times": [],
            "error_count": 0,
            "prediction_counts": {0: 0, 1: 0},
            "hourly_pattern": {str(h): 0 for h in range(24)}
        }
    
    daily_data = monitoring_history["time_metrics"]["daily"][day_key]
    daily_data["request_count"] += len(predictions)
    daily_data["success_count"] += sum(1 for p in predictions if p.get("success", False))
    daily_data["error_count"] += sum(1 for p in predictions if not p.get("success", False))
    daily_data["response_times"].extend([p.get("response_time", 0) for p in predictions if p.get("success", False)])
    daily_data["hourly_pattern"][str(current_time.hour)] += len(predictions)
    
    for p in predictions:
        if p.get("success", False) and p.get("outputs"):
            pred_value = p.get("outputs", [{}])[0].get("data", [0])[0]
            daily_data["prediction_counts"][pred_value] = daily_data["prediction_counts"].get(pred_value, 0) + 1
    
    # Weekly metrics - aggregated view
    if week_key not in monitoring_history["time_metrics"]["weekly"]:
        monitoring_history["time_metrics"]["weekly"][week_key] = {
            "request_count": 0,
            "success_count": 0,
            "avg_response_times": [],
            "error_count": 0,
            "daily_pattern": {str(d): 0 for d in range(7)}
        }
    
    weekly_data = monitoring_history["time_metrics"]["weekly"][week_key]
    weekly_data["request_count"] += len(predictions)
    weekly_data["success_count"] += sum(1 for p in predictions if p.get("success", False))
    weekly_data["error_count"] += sum(1 for p in predictions if not p.get("success", False))
    
    if metrics.get("avg_response_time"):
        weekly_data["avg_response_times"].append(metrics.get("avg_response_time"))
    
    # Day of week pattern (0=Monday, 6=Sunday)
    day_of_week = current_time.weekday()
    weekly_data["daily_pattern"][str(day_of_week)] += len(predictions)
    
    # Giới hạn kích thước lịch sử
    if len(monitoring_history["timestamps"]) > HISTORY_SIZE:
        monitoring_history["timestamps"] = monitoring_history["timestamps"][-HISTORY_SIZE:]
        monitoring_history["raw_timestamps"] = monitoring_history["raw_timestamps"][-HISTORY_SIZE:]
        monitoring_history["response_times"] = monitoring_history["response_times"][-HISTORY_SIZE:]
        monitoring_history["success_rates"] = monitoring_history["success_rates"][-HISTORY_SIZE:]
        monitoring_history["prediction_distributions"] = monitoring_history["prediction_distributions"][-HISTORY_SIZE:]
        monitoring_history["resource_usages"] = monitoring_history["resource_usages"][-HISTORY_SIZE:]
        
    # Xóa dữ liệu lịch sử cũ hơn TIME_WINDOW_HOURS
    cutoff_time = current_time - timedelta(hours=TIME_WINDOW_HOURS)
    for period in ["hourly", "daily", "weekly"]:
        keys_to_remove = []
        for key in monitoring_history["time_metrics"][period]:
            if period == "hourly":
                key_time = datetime.strptime(key, "%Y-%m-%d-%H")
                if key_time < cutoff_time:
                    keys_to_remove.append(key)
            elif period == "daily":
                key_time = datetime.strptime(key, "%Y-%m-%d")
                if key_time < cutoff_time - timedelta(days=7):  # Keep a week of daily data
                    keys_to_remove.append(key)
            # We keep all weekly data
        
        for key in keys_to_remove:
            del monitoring_history["time_metrics"][period][key]

def calculate_trend_metrics():
    """Tính toán các metrics xu hướng dựa trên lịch sử với tập trung vào yếu tố thời gian"""
    if len(monitoring_history["raw_timestamps"]) < 2:
        return {}
    
    trend_metrics = {}
    
    # Tính xu hướng thời gian phản hồi
    response_times = monitoring_history["response_times"]
    raw_timestamps = monitoring_history["raw_timestamps"]
    
    # Calculate time-based metrics if we have at least 2 data points
    if len(response_times) >= 2 and len(raw_timestamps) >= 2:
        # Tính tốc độ thay đổi theo thời gian (ms/giây)
        time_diff_seconds = (raw_timestamps[-1] - raw_timestamps[0]).total_seconds()
        if time_diff_seconds > 0:
            trend_metrics["response_time_change_rate"] = (response_times[-1] - response_times[0]) / time_diff_seconds
            
            # Tính percentage change
            if response_times[0] > 0:
                trend_metrics["response_time_percent_change"] = ((response_times[-1] / response_times[0]) - 1) * 100
    
    # Phân tích mẫu theo thời gian trong ngày
    hourly_metrics = monitoring_history["time_metrics"]["hourly"]
    if hourly_metrics:
        # Tìm giờ có response time cao nhất và thấp nhất
        hour_avg_response_times = {}
        for hour_key, data in hourly_metrics.items():
            if data["response_times"]:
                hour_avg_response_times[hour_key] = sum(data["response_times"]) / len(data["response_times"])
        
        if hour_avg_response_times:
            max_hour = max(hour_avg_response_times, key=hour_avg_response_times.get)
            min_hour = min(hour_avg_response_times, key=hour_avg_response_times.get)
            trend_metrics["max_response_time_hour"] = int(max_hour.split("-")[-1])
            trend_metrics["min_response_time_hour"] = int(min_hour.split("-")[-1])
            trend_metrics["hour_response_time_variation"] = hour_avg_response_times[max_hour] - hour_avg_response_times[min_hour]
    
    # Phân tích mẫu theo ngày trong tuần
    daily_metrics = monitoring_history["time_metrics"]["daily"]
    if daily_metrics:
        # Kiểm tra sự thay đổi theo ngày
        day_success_rates = {}
        for day_key, data in daily_metrics.items():
            if data["request_count"] > 0:
                day_success_rates[day_key] = (data["success_count"] / data["request_count"]) * 100
        
        if len(day_success_rates) >= 2:
            days = sorted(day_success_rates.keys())
            trend_metrics["daily_success_rate_change"] = day_success_rates[days[-1]] - day_success_rates[days[0]]
    
    # Tính toán mẫu thời gian response theo giờ
    hourly_pattern = [0] * 24
    hourly_counts = [0] * 24
    
    for hour_key, data in hourly_metrics.items():
        hour = int(hour_key.split("-")[-1])
        if data["response_times"]:
            hourly_pattern[hour] = sum(data["response_times"]) / len(data["response_times"])
            hourly_counts[hour] = len(data["response_times"])
    
    # Tìm peak times
    if sum(hourly_counts) > 0:
        peak_hour = hourly_counts.index(max(hourly_counts))
        trend_metrics["peak_request_hour"] = peak_hour
    
    if sum(hourly_pattern) > 0:
        peak_response_time_hour = hourly_pattern.index(max([t for t, c in zip(hourly_pattern, hourly_counts) if c > 0]))
        trend_metrics["peak_response_time_hour"] = peak_response_time_hour
    
    return trend_metrics

def log_detailed_metrics_to_mlflow(metrics, predictions, system_metrics, trend_metrics, health_check):
    """Log chi tiết metrics vào MLflow với tập trung vào các yếu tố thời gian"""
    mlflow = configure_mlflow("bank-churn-monitoring")
    
    with mlflow.start_run(nested=True):
        # Log metrics cơ bản
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                mlflow.log_metric(key, value)
        
        # Log thông tin chi tiết về thời gian
        current_time = datetime.now()
        
        # Log thời gian hiện tại chi tiết
        mlflow.log_metric("time.epoch", time.time())
        mlflow.log_metric("time.hour", current_time.hour)
        mlflow.log_metric("time.minute", current_time.minute)
        mlflow.log_metric("time.day_of_week", current_time.weekday())
        mlflow.log_metric("time.day_of_month", current_time.day)
        mlflow.log_metric("time.month", current_time.month)
        mlflow.log_metric("time.is_weekend", 1 if current_time.weekday() >= 5 else 0)
        mlflow.log_metric("time.is_business_hours", 1 if 8 <= current_time.hour <= 17 else 0)
        
        # Log quarter of the day (0-3: morning, afternoon, evening, night)
        quarter_of_day = current_time.hour // 6
        mlflow.log_metric("time.quarter_of_day", quarter_of_day)
        
        # Log time-based prediction distribution
        prediction_values = [p.get("outputs", [{}])[0].get("data", [0])[0] for p in predictions if p.get("success", False)]
        if prediction_values:
            mlflow.log_metric("predict_0_count", sum(1 for v in prediction_values if v == 0))
            mlflow.log_metric("predict_1_count", sum(1 for v in prediction_values if v == 1))
            mlflow.log_metric("predict_0_pct", sum(1 for v in prediction_values if v == 0) / len(prediction_values) * 100)
            mlflow.log_metric("predict_1_pct", sum(1 for v in prediction_values if v == 1) / len(prediction_values) * 100)
            
            # Log time-specific churn rates
            mlflow.log_metric(f"time.hour_{current_time.hour}.churn_rate", 
                             sum(1 for v in prediction_values if v == 1) / len(prediction_values) * 100)
            mlflow.log_metric(f"time.day_{current_time.weekday()}.churn_rate", 
                             sum(1 for v in prediction_values if v == 1) / len(prediction_values) * 100)
        
        # Log thông tin chi tiết về thời gian phản hồi
        response_times = [p.get("response_time", 0) for p in predictions if p.get("success", False)]
        if response_times:
            # Log percentiles và phân phối
            mlflow.log_metric("response_time_p50", np.percentile(response_times, 50))
            mlflow.log_metric("response_time_p90", np.percentile(response_times, 90))
            mlflow.log_metric("response_time_p95", np.percentile(response_times, 95))
            mlflow.log_metric("response_time_p99", np.percentile(response_times, 99))
            mlflow.log_metric("response_time_std", np.std(response_times))
            mlflow.log_metric("response_time_iqr", stats.iqr(response_times))
            
            # Log percentage trong SLA
            mlflow.log_metric("response_time_in_sla_pct", 
                             sum(1 for rt in response_times if rt <= MAX_RESPONSE_TIME_MS) / len(response_times) * 100)
            
            # Log time-specific response time
            mlflow.log_metric(f"time.hour_{current_time.hour}.avg_response_time", np.mean(response_times))
            mlflow.log_metric(f"time.day_{current_time.weekday()}.avg_response_time", np.mean(response_times))
            mlflow.log_metric(f"time.quarter_{quarter_of_day}.avg_response_time", np.mean(response_times))
        
        # Log system metrics with time context
        for key, value in system_metrics.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                mlflow.log_metric(f"system.{key}", value)
                # Log time-specific system metrics for key resources
                if key in ["cpu_percent", "memory_percent"]:
                    mlflow.log_metric(f"time.hour_{current_time.hour}.{key}", value)
        
        # Log trend metrics
        for key, value in trend_metrics.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                mlflow.log_metric(f"trend.{key}", value)
        
        # Log time-series metrics
        time_metrics = monitoring_history["time_metrics"]
        
        # Summarize hourly patterns
        if "hourly" in time_metrics and time_metrics["hourly"]:
            hourly_response_times = {}
            for hour_key, data in time_metrics["hourly"].items():
                if data["response_times"]:
                    hour = int(hour_key.split("-")[-1])
                    hourly_response_times[hour] = sum(data["response_times"]) / len(data["response_times"])
            
            for hour, avg_time in hourly_response_times.items():
                mlflow.log_metric(f"time_series.hour_{hour}.avg_response_time", avg_time)
        
        # Log batch metadata with time context
        batch_id = str(uuid.uuid4())
        mlflow.log_param("batch_id", batch_id)
        mlflow.log_param("batch_timestamp", current_time.isoformat())
        mlflow.log_param("batch_time_hour", current_time.hour)
        mlflow.log_param("batch_time_day", current_time.day)
        mlflow.log_param("batch_time_weekday", current_time.weekday())
        mlflow.log_param("batch_size", BATCH_SIZE)
        mlflow.log_param("monitoring_interval_minutes", MONITORING_INTERVAL_MINUTES)

def visualize_time_series_metrics():
    """Tạo các biểu đồ visualization để hiển thị metrics theo thời gian"""
    if len(monitoring_history["timestamps"]) < 2:
        return
    
    # Convert timestamps to datetime objects
    timestamps = [datetime.fromisoformat(ts) if isinstance(ts, str) else ts 
                 for ts in monitoring_history["raw_timestamps"]]
    
    # Create a DataFrame for time series visualization
    df = pd.DataFrame({
        'timestamp': timestamps,
        'response_time': monitoring_history["response_times"],
        'success_rate': monitoring_history["success_rates"],
        'hour': [ts.hour for ts in timestamps],
        'day_of_week': [ts.weekday() for ts in timestamps],
        'day': [ts.day for ts in timestamps]
    })
    
    # Set up the plots
    plt.figure(figsize=(12, 10))
    
    # 1. Response time over time
    plt.subplot(2, 2, 1)
    plt.plot(df['timestamp'], df['response_time'], marker='o', linestyle='-')
    plt.title('Response Time Trend')
    plt.xlabel('Time')
    plt.ylabel('Response Time (ms)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 2. Response time by hour of day
    plt.subplot(2, 2, 2)
    hour_groups = df.groupby('hour')['response_time'].mean()
    plt.bar(hour_groups.index, hour_groups.values)
    plt.title('Average Response Time by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Avg Response Time (ms)')
    plt.xticks(range(0, 24, 2))
    
    # 3. Success rate over time
    plt.subplot(2, 2, 3)
    plt.plot(df['timestamp'], df['success_rate'], marker='o', linestyle='-', color='green')
    plt.title('Success Rate Trend')
    plt.xlabel('Time')
    plt.ylabel('Success Rate (%)')
    plt.xticks(rotation=45)
    
    # 4. Response time by day of week
    plt.subplot(2, 2, 4)
    day_groups = df.groupby('day_of_week')['response_time'].mean()
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    plt.bar([days[i] for i in day_groups.index], day_groups.values, color='orange')
    plt.title('Average Response Time by Day of Week')
    plt.xlabel('Day')
    plt.ylabel('Avg Response Time (ms)')
    
    plt.tight_layout()
    plt.savefig('mlops_bigdata_2025II/bank_churn_test/monitoring/time_metrics.png')
    
    # Additional visualizations for hourly patterns
    if monitoring_history["time_metrics"]["hourly"]:
        plt.figure(figsize=(12, 6))
        
        # Prepare data
        hours = range(24)
        request_counts = [0] * 24
        avg_response_times = [0] * 24
        
        for hour_key, data in monitoring_history["time_metrics"]["hourly"].items():
            hour = int(hour_key.split('-')[-1])
            request_counts[hour] = data["request_count"]
            if data["response_times"]:
                avg_response_times[hour] = sum(data["response_times"]) / len(data["response_times"])
        
        # Plot request distribution by hour
        ax1 = plt.subplot(1, 2, 1)
        ax1.bar(hours, request_counts, color='blue', alpha=0.7)
        ax1.set_title('Request Distribution by Hour')
        ax1.set_xlabel('Hour of Day')
        ax1.set_ylabel('Number of Requests')
        ax1.set_xticks(range(0, 24, 2))
        
        # Plot response time by hour
        ax2 = plt.subplot(1, 2, 2)
        ax2.bar(hours, avg_response_times, color='red', alpha=0.7)
        ax2.set_title('Average Response Time by Hour')
        ax2.set_xlabel('Hour of Day')
        ax2.set_ylabel('Avg Response Time (ms)')
        ax2.set_xticks(range(0, 24, 2))
        
        plt.tight_layout()
        plt.savefig('mlops_bigdata_2025II/bank_churn_test/monitoring/hourly_patterns.png')
    
    print(f"Đã tạo biểu đồ time series metrics.")

def export_time_metrics_summary():
    """Xuất báo cáo tóm tắt về các metrics theo thời gian"""
    summary = {
        "general": {
            "total_batches": len(monitoring_history["timestamps"]),
            "monitoring_period": {
                "start": monitoring_history["timestamps"][0] if monitoring_history["timestamps"] else "",
                "end": monitoring_history["timestamps"][-1] if monitoring_history["timestamps"] else ""
            },
            "avg_response_time": np.mean(monitoring_history["response_times"]) if monitoring_history["response_times"] else 0,
            "avg_success_rate": np.mean(monitoring_history["success_rates"]) if monitoring_history["success_rates"] else 0
        },
        "time_patterns": {
            "hourly": {},
            "daily": {},
            "trend": calculate_trend_metrics()
        }
    }
    
    # Add hourly patterns
    hourly_metrics = monitoring_history["time_metrics"]["hourly"]
    for hour in range(24):
        hour_data = {
            "request_count": 0,
            "avg_response_time": 0,
            "success_rate": 0
        }
        
        # Find all entries for this hour across different days
        matching_hours = [
            data for hour_key, data in hourly_metrics.items() 
            if int(hour_key.split('-')[-1]) == hour and data["request_count"] > 0
        ]
        
        if matching_hours:
            hour_data["request_count"] = sum(d["request_count"] for d in matching_hours)
            total_response_time = sum(sum(d["response_times"]) for d in matching_hours if d["response_times"])
            total_response_count = sum(len(d["response_times"]) for d in matching_hours if d["response_times"])
            
            if total_response_count > 0:
                hour_data["avg_response_time"] = total_response_time / total_response_count
            
            total_success = sum(d["success_count"] for d in matching_hours)
            total_requests = sum(d["request_count"] for d in matching_hours)
            
            if total_requests > 0:
                hour_data["success_rate"] = (total_success / total_requests) * 100
        
        summary["time_patterns"]["hourly"][str(hour)] = hour_data
    
    # Add daily patterns
    daily_metrics = monitoring_history["time_metrics"]["daily"]
    for day in range(7):
        day_data = {
            "request_count": 0,
            "avg_response_time": 0,
            "success_rate": 0
        }
        
        # Process all matching days
        day_keys = [
            day_key for day_key in daily_metrics.keys() 
            if datetime.strptime(day_key, "%Y-%m-%d").weekday() == day
        ]
        
        matching_days = [daily_metrics[day_key] for day_key in day_keys if daily_metrics[day_key]["request_count"] > 0]
        
        if matching_days:
            day_data["request_count"] = sum(d["request_count"] for d in matching_days)
            total_response_time = sum(sum(d["response_times"]) for d in matching_days if d["response_times"])
            total_response_count = sum(len(d["response_times"]) for d in matching_days if d["response_times"])
            
            if total_response_count > 0:
                day_data["avg_response_time"] = total_response_time / total_response_count
            
            total_success = sum(d["success_count"] for d in matching_days)
            total_requests = sum(d["request_count"] for d in matching_days)
            
            if total_requests > 0:
                day_data["success_rate"] = (total_success / total_requests) * 100
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        summary["time_patterns"]["daily"][day_names[day]] = day_data
    
    # Save summary to file
    with open('mlops_bigdata_2025II/bank_churn_test/monitoring/time_metrics_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Đã xuất summary metrics theo thời gian.")

def run_monitoring_batch():
    """Thực hiện batch monitoring và log các metrics với tập trung vào yếu tố thời gian"""
    current_time = datetime.now()
    print(f"[{current_time}] Bắt đầu monitoring batch...")
    
    # Thu thập thông tin về tài nguyên hệ thống
    system_metrics = get_system_metrics()
    print(f"CPU: {system_metrics['cpu_percent']}%, Memory: {system_metrics['memory_percent']}%")
    
    # Kiểm tra sức khỏe model
    health = check_model_health()
    if not health["is_healthy"]:
        print(f"Model không khỏe mạnh. Status code: {health['status_code']}")
        
        # Log thông tin về lỗi model
        mlflow = configure_mlflow("bank-churn-monitoring")
        with mlflow.start_run(run_name="model-health-alert"):
            mlflow.log_param("error_timestamp", current_time.isoformat())
            mlflow.log_param("error_message", health.get("error", "Unknown error"))
            mlflow.log_metric("health_status", 0)
            mlflow.log_metric("status_code", health.get("status_code", 500))
            
            # Log time-based context for error
            mlflow.log_metric("time.hour", current_time.hour)
            mlflow.log_metric("time.day_of_week", current_time.weekday())
            mlflow.log_metric("time.day", current_time.day)
            mlflow.log_metric("time.month", current_time.month)
            
            # Log system metrics
            for key, value in system_metrics.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    mlflow.log_metric(f"system.{key}", value)
        
        return
    
    # Tạo dữ liệu test
    test_data = generate_test_data(BATCH_SIZE)
    
    # Thống kê đo lường
    prediction_distribution = {0: 0, 1: 0}
    response_times = []
    errors = 0
    predictions = []
    
    # Thực hiện dự đoán cho tất cả dữ liệu test
    batch_start_time = time.time()
    
    for i, data in enumerate(test_data):
        try:
            # Dự đoán
            prediction = predict_churn(data)
            predictions.append(prediction)
            
            if prediction.get("success", False):
                # Lấy giá trị dự đoán
                prediction_value = prediction["outputs"][0]["data"][0]
                
                # Cập nhật phân phối dự đoán
                if prediction_value in prediction_distribution:
                    prediction_distribution[prediction_value] += 1
                else:
                    prediction_distribution[prediction_value] = 1
                
                # Lưu thời gian phản hồi
                response_times.append(prediction["response_time"])
            else:
                errors += 1
                
        except Exception as e:
            print(f"Lỗi khi dự đoán mẫu {i}: {str(e)}")
            errors += 1
    
    batch_duration = time.time() - batch_start_time
    
    # Tính các metrics
    metrics = {
        "timestamp": time.time(),
        "batch_size": BATCH_SIZE,
        "errors": errors,
        "success_rate": (BATCH_SIZE - errors) / BATCH_SIZE * 100,
        "batch_duration": batch_duration * 1000,  # Convert to ms
        "batch_throughput": BATCH_SIZE / (batch_duration if batch_duration > 0 else 1)  # Requests per second
    }
    
    # Time-of-day metrics
    metrics.update({
        "hour_of_day": current_time.hour,
        "day_of_week": current_time.weekday(),
        "is_business_hours": 1 if 8 <= current_time.hour <= 17 else 0,
        "is_weekend": 1 if current_time.weekday() >= 5 else 0
    })
    
    # Metrics về thời gian phản hồi
    if response_times:
        metrics.update({
            "avg_response_time": statistics.mean(response_times),
            "max_response_time": max(response_times),
            "min_response_time": min(response_times),
            "p95_response_time": np.percentile(response_times, 95),
            "p99_response_time": np.percentile(response_times, 99),
            "median_response_time": np.median(response_times),
            "response_time_std": np.std(response_times),
            "response_time_sla_breaches": sum(1 for t in response_times if t > MAX_RESPONSE_TIME_MS),
            "response_time_sla_breach_pct": sum(1 for t in response_times if t > MAX_RESPONSE_TIME_MS) / len(response_times) * 100
        })
    
    # Metrics về phân phối dự đoán
    for value, count in prediction_distribution.items():
        metrics[f"predict_{value}_count"] = count
        metrics[f"predict_{value}_pct"] = count / BATCH_SIZE * 100
    
    # Cập nhật lịch sử monitoring
    update_monitoring_history(metrics, predictions)
    
    # Tính toán các metrics xu hướng
    trend_metrics = calculate_trend_metrics()
    
    # Log vào MLflow - sửa lỗi run đã active
    try:
        # Đảm bảo không có run đang hoạt động
        mlflow = configure_mlflow("bank-churn-monitoring")
        ensure_no_active_runs()
        
        with mlflow.start_run(run_name=f"monitor-batch-{current_time.strftime('%Y%m%d-%H%M%S')}") as run:
            # Log detailed metrics
            log_detailed_metrics_to_mlflow(metrics, predictions, system_metrics, trend_metrics, health)
    except Exception as e:
        print(f"Lỗi khi log metrics: {str(e)}")
        # Đảm bảo kết thúc bất kỳ run nào đang active
        try:
            mlflow.end_run()
        except:
            pass
    
    # Tạo visualization cho time-based metrics sau mỗi 5 lần chạy (để tránh quá nhiều I/O)
    if len(monitoring_history["timestamps"]) % 5 == 0:
        try:
            visualize_time_series_metrics()
            export_time_metrics_summary()
        except Exception as e:
            print(f"Lỗi khi tạo visualizations: {str(e)}")
    
    print(f"[{current_time}] Đã hoàn thành monitoring batch.")
    print(f"Thời gian phản hồi trung bình: {metrics.get('avg_response_time', 'N/A'):.2f} ms")
    print(f"Thời gian xử lý batch: {metrics.get('batch_duration', 'N/A'):.2f} ms")
    print(f"Throughput: {metrics.get('batch_throughput', 'N/A'):.2f} requests/second")
    print(f"Tỷ lệ thành công: {metrics.get('success_rate', 'N/A'):.2f}%")
    print(f"Phân phối dự đoán: {prediction_distribution}")
    
    # Log thông tin về giờ trong ngày và mẫu
    print(f"\nThông tin về thời gian:")
    print(f"  Giờ hiện tại: {current_time.hour}:00")
    print(f"  Ngày trong tuần: {['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'][current_time.weekday()]}")
    print(f"  Thời gian làm việc: {'Có' if 8 <= current_time.hour <= 17 else 'Không'}")
    
    # Log xu hướng
    if trend_metrics:
        print("\nXu hướng theo thời gian:")
        for key, value in trend_metrics.items():
            print(f"  {key}: {value:.4f}")

def start_scheduler():
    """Bắt đầu lịch trình monitoring định kỳ với tập trung vào các mẫu theo thời gian"""
    # Schedule monitoring at fixed intervals
    schedule.every(MONITORING_INTERVAL_MINUTES).minutes.do(run_monitoring_batch)
    
    # Add time-specific monitoring to capture patterns throughout the day
    for hour in [9, 12, 15, 18, 21]:  # Specific hours to monitor (9am, 12pm, 3pm, 6pm, 9pm)
        schedule.every().day.at(f"{hour:02d}:00").do(run_monitoring_batch)
    
    # Add monitoring for weekday vs weekend comparison
    schedule.every().saturday.at("12:00").do(run_monitoring_batch)
    schedule.every().sunday.at("12:00").do(run_monitoring_batch)
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    print(f"[{datetime.now()}] Bắt đầu chương trình monitoring model với tập trung vào yếu tố thời gian...")
    
    # Đảm bảo không có run đang bị treo
    ensure_no_active_runs()
    
    # Tạo thư mục cho visualizations nếu chưa tồn tại
    os.makedirs('mlops_bigdata_2025II/bank_churn_test/monitoring', exist_ok=True)
    
    # Chạy đợt monitoring đầu tiên ngay lập tức
    run_monitoring_batch()
    
    # Bắt đầu lịch trình monitor định kỳ
    print(f"Đã lên lịch monitoring theo mẫu thời gian")
    print(f"- Monitoring định kỳ: mỗi {MONITORING_INTERVAL_MINUTES} phút")
    print(f"- Monitoring theo giờ cụ thể: 9:00, 12:00, 15:00, 18:00, 21:00")
    print(f"- Monitoring cuối tuần: 12:00 thứ 7 và chủ nhật")
    
    try:
        # Bắt đầu scheduler trong một thread riêng
        scheduler_thread = threading.Thread(target=start_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        # Giữ chương trình chạy (có thể thêm logic để dừng chương trình nếu cần)
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("Đã nhận lệnh dừng. Kết thúc chương trình.")
        # Đảm bảo đóng tất cả các active run trước khi thoát
        try:
            mlflow.end_run()
        except:
            pass
    
    # Export final summary before exiting
    export_time_metrics_summary()

if __name__ == "__main__":
    main()