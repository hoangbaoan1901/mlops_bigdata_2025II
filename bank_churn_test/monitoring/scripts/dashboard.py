#!/usr/bin/env python
import sys
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.mlflow_config import configure_mlflow

def get_experiment_runs(mlflow, experiment_name, max_runs=200):
    """Get runs from an experiment"""
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if not experiment:
        print(f"Experiment {experiment_name} not found")
        return None
    
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        max_results=max_runs,
        order_by=["attribute.start_time DESC"]
    )
    
    return runs

def plot_metrics_over_time(runs, metric_names, title, figsize=(12, 8)):
    """Vẽ biểu đồ metrics theo thời gian"""
    if runs.empty:
        print(f"No runs found for {title}")
        return
    
    # Sắp xếp theo thời gian
    runs = runs.sort_values('start_time')
    
    # Tạo dữ liệu thời gian
    start_times = pd.to_datetime(runs['start_time'])
    
    plt.figure(figsize=figsize)
    
    for metric in metric_names:
        if metric in runs.columns:
            plt.plot(start_times, runs[metric], marker='o', label=metric)
    
    plt.title(title)
    plt.xlabel('Thời gian')
    plt.ylabel('Giá trị')
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Lưu biểu đồ
    filename = f"{title.lower().replace(' ', '_')}.png"
    plt.savefig(filename)
    print(f"Saved chart to {filename}")
    
    plt.close()

def plot_prediction_distribution(runs, figsize=(12, 6)):
    """Vẽ biểu đồ phân phối dự đoán"""
    if runs.empty:
        print("No prediction distribution data found")
        return
    
    # Check for columns
    churn_col = None
    non_churn_col = None
    
    if 'metrics.predict_1_pct' in runs.columns:
        churn_col = 'metrics.predict_1_pct'
        non_churn_col = 'metrics.predict_0_pct'
    elif 'metrics.batch.churn_rate' in runs.columns:
        churn_col = 'metrics.batch.churn_rate'
    elif 'metrics.prediction.value' in runs.columns:
        # Calculate from individual predictions
        total_preds = len(runs)
        churn_count = sum(1 for v in runs['metrics.prediction.value'] if v == 1)
        runs['calculated_churn_rate'] = churn_count / total_preds * 100
        churn_col = 'calculated_churn_rate'
    
    if not churn_col:
        print("No suitable prediction data found")
        return
    
    # Sắp xếp theo thời gian
    runs = runs.sort_values('start_time')
    
    # Tạo dữ liệu thời gian
    start_times = pd.to_datetime(runs['start_time'])
    
    plt.figure(figsize=figsize)
    
    # Prepare data
    churn_rates = runs[churn_col]
    if churn_col == 'metrics.batch.churn_rate':
        churn_rates = churn_rates * 100  # Convert to percentage
    
    if non_churn_col and non_churn_col in runs.columns:
        non_churn_rates = runs[non_churn_col]
    else:
        non_churn_rates = 100 - churn_rates
    
    plt.stackplot(start_times, [non_churn_rates, churn_rates], 
                 labels=['Non-Churn (0)', 'Churn (1)'],
                 colors=['green', 'red'], alpha=0.7)
    
    plt.title('Phân phối dự đoán theo thời gian')
    plt.xlabel('Thời gian')
    plt.ylabel('Phần trăm (%)')
    plt.ylim(0, 100)
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Lưu biểu đồ
    filename = "prediction_distribution.png"
    plt.savefig(filename)
    print(f"Saved prediction distribution chart to {filename}")
    
    plt.close()

def plot_response_time_distribution(runs, figsize=(12, 6)):
    """Vẽ biểu đồ phân phối thời gian phản hồi"""
    if runs.empty:
        return
    
    response_time_cols = [col for col in runs.columns if 'response_time' in col and col != 'metrics.response_time_sla_breaches']
    
    if not response_time_cols:
        print("No response time data found")
        return
    
    # Lấy dữ liệu thời gian phản hồi từ cột đầu tiên tìm thấy
    response_time_col = response_time_cols[0]
    response_times = runs[response_time_col].dropna()
    
    if len(response_times) == 0:
        return
    
    plt.figure(figsize=figsize)
    
    # Vẽ histogram
    plt.hist(response_times, bins=20, alpha=0.7, color='blue')
    
    plt.axvline(response_times.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {response_times.mean():.2f} ms')
    plt.axvline(response_times.median(), color='green', linestyle='dashed', linewidth=2, label=f'Median: {response_times.median():.2f} ms')
    
    # Thêm ngưỡng SLA nếu có
    sla_col = next((col for col in runs.columns if 'sla' in col.lower()), None)
    if sla_col:
        sla_value = 1000  # Default value
        plt.axvline(sla_value, color='orange', linestyle='dashed', linewidth=2, label=f'SLA: {sla_value} ms')
    
    plt.title('Phân phối thời gian phản hồi')
    plt.xlabel('Thời gian phản hồi (ms)')
    plt.ylabel('Số lượng')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    
    # Lưu biểu đồ
    filename = "response_time_distribution.png"
    plt.savefig(filename)
    print(f"Saved response time distribution chart to {filename}")
    
    plt.close()

def plot_system_metrics(runs, figsize=(15, 10)):
    """Vẽ biểu đồ metrics hệ thống"""
    if runs.empty:
        return
    
    system_metrics = [col for col in runs.columns if 'system' in col]
    
    if not system_metrics:
        print("No system metrics found")
        return
    
    # Sắp xếp theo thời gian
    runs = runs.sort_values('start_time')
    
    # Tạo dữ liệu thời gian
    start_times = pd.to_datetime(runs['start_time'])
    
    # Tạo các subplot
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle('System Metrics Over Time', fontsize=16)
    
    # CPU usage
    cpu_col = next((col for col in system_metrics if 'cpu' in col), None)
    if cpu_col and cpu_col in runs.columns:
        axes[0, 0].plot(start_times, runs[cpu_col], marker='o', color='red')
        axes[0, 0].set_title('CPU Usage (%)')
        axes[0, 0].set_ylabel('Percentage')
        axes[0, 0].grid(True)
        axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Memory usage
    memory_col = next((col for col in system_metrics if 'memory_percent' in col), None)
    if memory_col and memory_col in runs.columns:
        axes[0, 1].plot(start_times, runs[memory_col], marker='o', color='blue')
        axes[0, 1].set_title('Memory Usage (%)')
        axes[0, 1].set_ylabel('Percentage')
        axes[0, 1].grid(True)
        axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Disk usage
    disk_col = next((col for col in system_metrics if 'disk' in col), None)
    if disk_col and disk_col in runs.columns:
        axes[1, 0].plot(start_times, runs[disk_col], marker='o', color='green')
        axes[1, 0].set_title('Disk Usage (%)')
        axes[1, 0].set_ylabel('Percentage')
        axes[1, 0].grid(True)
        axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Available memory
    avail_memory_col = next((col for col in system_metrics if 'memory_available' in col), None)
    if avail_memory_col and avail_memory_col in runs.columns:
        axes[1, 1].plot(start_times, runs[avail_memory_col], marker='o', color='purple')
        axes[1, 1].set_title('Available Memory (MB)')
        axes[1, 1].set_ylabel('MB')
        axes[1, 1].grid(True)
        axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Để không chồng lên cái title chính
    
    # Lưu biểu đồ
    filename = "system_metrics.png"
    plt.savefig(filename)
    print(f"Saved system metrics chart to {filename}")
    
    plt.close()

def generate_summary_report(mlflow, experiment_name):
    """Tạo báo cáo tổng hợp cho một experiment"""
    print(f"\n===== Generating report for experiment: {experiment_name} =====\n")
    
    # Lấy runs
    runs = get_experiment_runs(mlflow, experiment_name)
    
    if runs is None or runs.empty:
        print(f"No runs found for experiment '{experiment_name}'")
        return
    
    # Lấy các loại metrics có trong dữ liệu
    metric_columns = [col for col in runs.columns if col.startswith('metrics.')]
    
    # In thông tin
    print(f"Total runs: {len(runs)}")
    print(f"Time range: {runs['start_time'].min()} to {runs['start_time'].max()}")
    print(f"Available metrics: {len(metric_columns)}")
    
    # Vẽ biểu đồ response time
    response_time_metrics = [col for col in metric_columns if 'response_time' in col 
                           and not any(x in col for x in ['p90', 'p95', 'p99', 'std', 'iqr', 'skew'])]
    if response_time_metrics:
        plot_metrics_over_time(runs, response_time_metrics, 'Response Time Metrics')
    
    # Vẽ biểu đồ success rate
    success_rate_metrics = [col for col in metric_columns if 'success_rate' in col or 'success' in col]
    if success_rate_metrics:
        plot_metrics_over_time(runs, success_rate_metrics, 'Success Rate Metrics')
    
    # Vẽ biểu đồ phân phối dự đoán
    plot_prediction_distribution(runs)
    
    # Vẽ biểu đồ phân phối thời gian phản hồi
    plot_response_time_distribution(runs)
    
    # Vẽ biểu đồ system metrics
    plot_system_metrics(runs)
    
    # In các xu hướng metrics nếu có
    trend_metrics = [col for col in metric_columns if 'trend' in col]
    if trend_metrics:
        print("\nTrend metrics:")
        for metric in trend_metrics:
            last_value = runs.sort_values('start_time', ascending=False)[metric].iloc[0]
            metric_name = metric.replace('metrics.trend.', '')
            direction = "upward" if last_value > 0 else "downward" if last_value < 0 else "stable"
            print(f"  {metric_name}: {last_value:.4f} ({direction} trend)")
    
    print("\nReport generation complete!")

def main():
    parser = argparse.ArgumentParser(description='Generate MLflow metrics dashboard')
    parser.add_argument('--experiment', type=str, help='Experiment name to analyze')
    args = parser.parse_args()
    
    # Cấu hình MLflow
    mlflow = configure_mlflow()
    print(f"Connected to MLflow tracking server")
    
    # Liệt kê các experiments nếu không chỉ định experiment
    if not args.experiment:
        experiments = mlflow.search_experiments()
        print("\nAvailable experiments:")
        for exp in experiments:
            print(f"  {exp.name} (ID: {exp.experiment_id})")
        
        # Chọn experiment để phân tích
        experiment_name = input("\nEnter experiment name to analyze: ")
    else:
        experiment_name = args.experiment
    
    # Tạo báo cáo
    generate_summary_report(mlflow, experiment_name)

if __name__ == "__main__":
    main()