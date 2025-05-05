import logging
import subprocess
import threading
import time
from typing import List, Dict, Optional, Any
from ..models.base_models import MLflowConfig

logger = logging.getLogger(__name__)

class MLflowService:
    """Service for managing MLflow server"""
    
    def __init__(self):
        self.mlflow_process = None
        self.mlflow_status = "stopped"
        self.mlflow_logs = []
        self.mlflow_config = None
        self.log_lock = threading.Lock()
    
    def start_server(self, config: MLflowConfig) -> bool:
        """Start MLflow server
        
        Args:
            config: MLflow configuration
            
        Returns:
            True if server started successfully
        """
        if self.mlflow_status == "running":
            logger.warning("MLflow server is already running")
            return False
        
        self.mlflow_config = config
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=self._start_mlflow_server, args=(config,))
        server_thread.daemon = True
        server_thread.start()
        
        return True
    
    def stop_server(self) -> bool:
        """Stop MLflow server
        
        Returns:
            True if server stopped successfully
        """
        if self.mlflow_status == "stopped":
            logger.warning("MLflow server is not running")
            return False
        
        try:
            if self.mlflow_process:
                self.mlflow_process.terminate()
                self.mlflow_process.wait()
                self.mlflow_process = None
            
            self.mlflow_status = "stopped"
            self._add_log("MLflow server stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping MLflow server: {str(e)}")
            self._add_log(f"Error stopping MLflow server: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get MLflow server status
        
        Returns:
            Server status information
        """
        if self.mlflow_status == "running" and self.mlflow_config:
            return {
                "status": self.mlflow_status,
                "url": f"http://localhost:{self.mlflow_config.port}",
                "message": "MLflow server is running"
            }
        else:
            return {
                "status": self.mlflow_status,
                "message": "MLflow server is not running"
            }
    
    def get_logs(self) -> List[str]:
        """Get MLflow server logs
        
        Returns:
            List of log lines
        """
        with self.log_lock:
            return self.mlflow_logs.copy()
    
    def _add_log(self, message: str):
        """Add a message to the log
        
        Args:
            message: Log message
        """
        with self.log_lock:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.mlflow_logs.append(log_entry)
            logger.info(message)
    
    def _start_mlflow_server(self, config: MLflowConfig):
        """Start MLflow server process
        
        Args:
            config: MLflow configuration
        """
        try:
            # Build command
            cmd = [
                "mlflow", "server",
                "--host", config.host,
                "--port", str(config.port),
                "--default-artifact-root", config.artifact_uri
            ]
            
            if config.backend_store_uri:
                cmd.extend(["--backend-store-uri", config.backend_store_uri])
            
            # Update status
            self.mlflow_status = "starting"
            self._add_log(f"Starting MLflow server with command: {' '.join(cmd)}")
            
            # Start process
            self.mlflow_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Wait for startup
            time.sleep(2)
            
            # Check if process is still running
            if self.mlflow_process.poll() is None:
                self.mlflow_status = "running"
                self._add_log(f"MLflow server started successfully on port {config.port}")
            else:
                self.mlflow_status = "stopped"
                output, _ = self.mlflow_process.communicate()
                self._add_log(f"MLflow server failed to start: {output}")
                self.mlflow_process = None
                return
            
            # Read output continuously
            for line in iter(self.mlflow_process.stdout.readline, ''):
                self._add_log(line.strip())
                
                # Check if process has ended
                if self.mlflow_process.poll() is not None:
                    break
            
            # Process ended
            returncode = self.mlflow_process.wait()
            self.mlflow_status = "stopped"
            self._add_log(f"MLflow server process ended with code {returncode}")
            self.mlflow_process = None
        
        except Exception as e:
            self.mlflow_status = "stopped"
            self._add_log(f"Error in MLflow server process: {str(e)}")
            logger.error(f"Error in MLflow server process: {str(e)}")
            if self.mlflow_process:
                try:
                    self.mlflow_process.terminate()
                except:
                    pass
                self.mlflow_process = None 