#!/usr/bin/env python
import psutil
import platform
import socket
import time
import uuid

def get_system_metrics():
    """Thu thập thông tin về tài nguyên hệ thống"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "system_time": time.time(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "network_connections": len(psutil.net_connections())
    }

def get_system_info():
    """Thu thập thông tin về hệ thống"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                for elements in range(0, 48, 8)][::-1]),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
    }

def log_system_load(interval=5, duration=60):
    """Log system load over a period of time"""
    start_time = time.time()
    end_time = start_time + duration
    
    metrics_history = []
    
    while time.time() < end_time:
        metrics = get_system_metrics()
        metrics["timestamp"] = time.time()
        metrics_history.append(metrics)
        
        time.sleep(interval)
    
    return metrics_history