import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class KubeflowService:
    """Service for interacting with Kubeflow Pipelines"""
    
    def get_port_forward_command(self, namespace: str, service: str, port: int) -> str:
        """Get the kubectl port-forward command for accessing Kubeflow UI
        
        Args:
            namespace: Kubernetes namespace where Kubeflow is deployed
            service: Kubeflow UI service name
            port: Port to forward to
            
        Returns:
            Port-forward command string
        """
        return f"kubectl port-forward -n {namespace} svc/{service} {port}:80"
    
    def check_connection(self, port: int) -> Dict[str, Any]:
        """Check if Kubeflow UI is accessible
        
        Args:
            port: Port where Kubeflow UI should be accessible
            
        Returns:
            Connection status information
        """
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=2)
            if response.status_code == 200:
                return {
                    "connected": True, 
                    "url": f"http://localhost:{port}/"
                }
            else:
                return {
                    "connected": False, 
                    "error": f"Received status code {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error checking Kubeflow connection: {str(e)}")
            return {
                "connected": False, 
                "error": str(e)
            } 