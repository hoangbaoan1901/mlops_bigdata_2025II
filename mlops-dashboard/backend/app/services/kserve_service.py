import os
import logging
from kubernetes import client, config
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class KServeService:
    """Service for interacting with KServe through Kubernetes API"""
    
    def __init__(self):
        """Initialize the KServe service"""
        try:
            # Try to load cluster config if running in-cluster
            config.load_incluster_config()
        except:
            # Fallback to kubeconfig
            try:
                config.load_kube_config()
            except:
                logger.warning("Could not configure Kubernetes client, running in mock mode")
        
        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        self.app_api = client.AppsV1Api()
    
    def get_inference_services(self, namespace=None) -> List[Dict[str, Any]]:
        """Get all KServe InferenceServices in specified namespace or across namespaces
        
        Args:
            namespace: Kubernetes namespace (None to get from all accessible namespaces)
            
        Returns:
            List of InferenceService details
        """
        try:
            results = []
            
            # Danh sách namespace cần quét, nếu không chỉ định thì ưu tiên bankchurn-kserve-2 và default
            namespaces_to_check = []
            if namespace:
                namespaces_to_check.append(namespace)
            else:
                # Ưu tiên namespace bankchurn-kserve-2
                namespaces_to_check.append("bankchurn-kserve-2")
                namespaces_to_check.append("default")
                
                # Thử lấy tất cả các namespace mà client có quyền truy cập
                try:
                    all_namespaces = self.core_api.list_namespace()
                    for ns in all_namespaces.items:
                        ns_name = ns.metadata.name
                        if ns_name not in namespaces_to_check:
                            namespaces_to_check.append(ns_name)
                except Exception as e:
                    logger.warning(f"Cannot list all namespaces, will use default ones: {str(e)}")
            
            # Lấy InferenceServices từ các namespace
            for ns in namespaces_to_check:
                try:
                    response = self.custom_api.list_namespaced_custom_object(
                        group="serving.kserve.io",
                        version="v1beta1",
                        namespace=ns,
                        plural="inferenceservices"
                    )
                    
                    for item in response.get("items", []):
                        service = {
                            "name": item["metadata"]["name"],
                            "namespace": item["metadata"]["namespace"],
                            "created": item["metadata"]["creationTimestamp"],
                            "model_uri": self._extract_model_uri(item),
                            "framework": self._extract_framework(item),
                            "version": item["metadata"].get("resourceVersion", "unknown"),
                            "status": self._extract_status(item),
                            "endpoint": self._extract_endpoint(item),
                            "replicas": self._extract_replicas(item),
                            "resources": self._extract_resources(item),
                            "traffic": self._extract_traffic(item),
                            "error": self._extract_error(item),
                            "serviceAccountName": self._extract_service_account(item)
                        }
                        results.append(service)
                except Exception as e:
                    logger.warning(f"Error listing InferenceServices in namespace {ns}: {str(e)}")
                    continue
                    
            return results
        except Exception as e:
            logger.error(f"Error retrieving InferenceServices: {str(e)}")
            return []
    
    def get_inference_service(self, name: str, namespace="default") -> Optional[Dict[str, Any]]:
        """Get a specific KServe InferenceService
        
        Args:
            name: Name of the InferenceService
            namespace: Kubernetes namespace
            
        Returns:
            InferenceService details or None if not found
        """
        try:
            item = self.custom_api.get_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=name
            )
            
            service = {
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "created": item["metadata"]["creationTimestamp"],
                "model_uri": self._extract_model_uri(item),
                "framework": self._extract_framework(item),
                "version": item["metadata"].get("resourceVersion", "unknown"),
                "status": self._extract_status(item),
                "endpoint": self._extract_endpoint(item),
                "replicas": self._extract_replicas(item),
                "resources": self._extract_resources(item),
                "traffic": self._extract_traffic(item),
                "error": self._extract_error(item),
                "serviceAccountName": self._extract_service_account(item)
            }
            
            return service
        except client.rest.ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"API error retrieving InferenceService {name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving InferenceService {name}: {str(e)}")
            return None
    
    def create_inference_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new KServe InferenceService
        
        Args:
            data: InferenceService definition
            
        Returns:
            Created InferenceService details
        """
        try:
            name = data["name"]
            namespace = data.get("namespace", "default")
            model_uri = data["model_uri"]
            framework = data.get("framework", "tensorflow")
            replicas = data.get("replicas", 1)
            resources = data.get("resources", {"cpu": "1", "memory": "2Gi"})
            serviceAccountName = data.get("serviceAccountName")
            
            # Prepare spec based on framework
            predictor = self._get_predictor_for_framework(
                framework, 
                model_uri, 
                resources, 
                replicas,
                serviceAccountName
            )
            
            # Build InferenceService spec
            inference_service = {
                "apiVersion": "serving.kserve.io/v1beta1",
                "kind": "InferenceService",
                "metadata": {
                    "name": name,
                    "namespace": namespace
                },
                "spec": {
                    "predictor": predictor
                }
            }
            
            # Create the InferenceService
            response = self.custom_api.create_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                body=inference_service
            )
            
            # Return formatted service
            return self.get_inference_service(name, namespace) or {}
        except Exception as e:
            logger.error(f"Error creating InferenceService: {str(e)}")
            raise
    
    def delete_inference_service(self, name: str, namespace="default") -> bool:
        """Delete a KServe InferenceService
        
        Args:
            name: Name of the InferenceService
            namespace: Kubernetes namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=name
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting InferenceService {name}: {str(e)}")
            return False
    
    def get_inference_service_logs(self, name: str, namespace="default") -> List[str]:
        """Get logs from a specific InferenceService
        
        Args:
            name: Name of the InferenceService
            namespace: Kubernetes namespace
            
        Returns:
            List of log lines
        """
        try:
            # Find pods associated with the InferenceService
            label_selector = f"serving.kserve.io/inferenceservice={name}"
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            logs = []
            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_logs = self.core_api.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    container="kserve-container",  # Typically the main container for inferenceservice
                    tail_lines=100
                )
                logs.extend(pod_logs.split("\n"))
            
            return logs
        except Exception as e:
            logger.error(f"Error getting logs for InferenceService {name}: {str(e)}")
            return [f"Error fetching logs: {str(e)}"]
    
    def get_serving_runtimes(self, namespace=None) -> List[Dict[str, Any]]:
        """Get available KServe ServingRuntimes
        
        Args:
            namespace: Optional namespace to filter runtimes
            
        Returns:
            List of ServingRuntime details
        """
        try:
            results = []
            
            # Tìm kiếm ServingRuntimes trong cụm (cluster-wide)
            try:
                response = self.custom_api.list_cluster_custom_object(
                    group="serving.kserve.io",
                    version="v1alpha1",
                    plural="servingruntimes"
                )
                
                for item in response.get("items", []):
                    runtime = {
                        "name": item["metadata"]["name"],
                        "framework": self._extract_runtime_framework(item),
                        "version": item["spec"].get("supportedModelFormats", [{}])[0].get("version", "unknown"),
                        "status": "Available" if item.get("status", {}).get("conditions", [{}])[0].get("status") == "True" else "Unavailable",
                        "scope": "Cluster"
                    }
                    results.append(runtime)
            except Exception as e:
                logger.warning(f"Error retrieving cluster-wide ServingRuntimes: {str(e)}")
            
            # Tìm kiếm ServingRuntimes trong các namespace cụ thể
            namespaces_to_check = []
            if namespace:
                namespaces_to_check.append(namespace)
            else:
                # Ưu tiên namespace bankchurn-kserve-2
                namespaces_to_check.append("bankchurn-kserve-2")
                namespaces_to_check.append("default")
                namespaces_to_check.append("kserve")
                
                # Thử lấy tất cả các namespace mà client có quyền truy cập
                try:
                    all_namespaces = self.core_api.list_namespace()
                    for ns in all_namespaces.items:
                        ns_name = ns.metadata.name
                        if ns_name not in namespaces_to_check:
                            namespaces_to_check.append(ns_name)
                except Exception as e:
                    logger.warning(f"Cannot list all namespaces, will use default ones: {str(e)}")
            
            # Kiểm tra ServingRuntimes trong từng namespace
            for ns in namespaces_to_check:
                try:
                    response = self.custom_api.list_namespaced_custom_object(
                        group="serving.kserve.io",
                        version="v1alpha1",
                        namespace=ns,
                        plural="servingruntimes"
                    )
                    
                    for item in response.get("items", []):
                        runtime = {
                            "name": item["metadata"]["name"],
                            "namespace": ns,
                            "framework": self._extract_runtime_framework(item),
                            "version": item["spec"].get("supportedModelFormats", [{}])[0].get("version", "unknown"),
                            "status": "Available" if item.get("status", {}).get("conditions", [{}])[0].get("status") == "True" else "Unavailable",
                            "scope": "Namespaced"
                        }
                        results.append(runtime)
                except Exception as e:
                    logger.debug(f"Error listing ServingRuntimes in namespace {ns}: {str(e)}")
                    continue
            
            # Trả về kết quả thực tế, không tạo dữ liệu mẫu
            return results
        except Exception as e:
            logger.error(f"Error retrieving ServingRuntimes: {str(e)}")
            return []
    
    # Helper methods to extract data from InferenceService objects
    
    def _extract_model_uri(self, item: Dict[str, Any]) -> str:
        """Extract model URI from InferenceService"""
        predictor = item.get("spec", {}).get("predictor", {})
        
        # Check if using KServe model format
        if "model" in predictor:
            return predictor["model"].get("storageUri", "unknown")
            
        # Check for framework-specific predictor containers
        for key in ["tensorflow", "pytorch", "sklearn", "xgboost", "onnx"]:
            if key in predictor:
                return predictor[key].get("storageUri", "unknown")
                
        return "unknown"
    
    def _extract_framework(self, item: Dict[str, Any]) -> str:
        """Extract framework from InferenceService"""
        predictor = item.get("spec", {}).get("predictor", {})
        
        # Check if using KServe model format
        if "model" in predictor:
            model_format = predictor["model"].get("modelFormat", {})
            if model_format.get("name"):
                return model_format.get("name").lower()
        
        # Check for framework-specific predictor containers
        for key in ["tensorflow", "pytorch", "sklearn", "xgboost", "onnx"]:
            if key in predictor:
                return key
                
        return "unknown"
    
    def _extract_status(self, item: Dict[str, Any]) -> str:
        """Extract status from InferenceService"""
        conditions = item.get("status", {}).get("conditions", [])
        if not conditions:
            return "Unknown"
        
        ready_condition = next((c for c in conditions if c.get("type") == "Ready"), None)
        if not ready_condition:
            return "Unknown"
        
        if ready_condition.get("status") == "True":
            return "Running"
        elif ready_condition.get("status") == "False":
            return "Failed"
        else:
            return "Creating"
    
    def _extract_endpoint(self, item: Dict[str, Any]) -> str:
        """Extract endpoint URL from InferenceService"""
        return item.get("status", {}).get("url", "unknown")
    
    def _extract_replicas(self, item: Dict[str, Any]) -> int:
        """Extract replica count from InferenceService"""
        return item.get("spec", {}).get("predictor", {}).get("minReplicas", 0)
    
    def _extract_resources(self, item: Dict[str, Any]) -> Dict[str, str]:
        """Extract resource requirements from InferenceService"""
        predictor = item.get("spec", {}).get("predictor", {})
        resources = {}
        
        # Extract framework-specific resources
        for key in ["tensorflow", "pytorch", "sklearn", "xgboost", "onnx"]:
            if key in predictor:
                container_resources = predictor[key].get("resources", {})
                limits = container_resources.get("limits", {})
                requests = container_resources.get("requests", {})
                
                resources = {
                    "cpu": limits.get("cpu", requests.get("cpu", "unknown")),
                    "memory": limits.get("memory", requests.get("memory", "unknown"))
                }
                
                # Add GPU if available
                if "nvidia.com/gpu" in limits:
                    resources["gpu"] = limits["nvidia.com/gpu"]
                
                break
        
        return resources or {"cpu": "unknown", "memory": "unknown"}
    
    def _extract_traffic(self, item: Dict[str, Any]) -> int:
        """Extract traffic percentage from InferenceService"""
        return item.get("status", {}).get("components", {}).get("predictor", {}).get("traffic", 100)
    
    def _extract_error(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract error message if any from InferenceService"""
        conditions = item.get("status", {}).get("conditions", [])
        failed_condition = next((c for c in conditions if c.get("status") == "False" and c.get("message")), None)
        
        if failed_condition:
            return failed_condition.get("message")
        return None
    
    def _extract_runtime_framework(self, item: Dict[str, Any]) -> str:
        """Extract framework from ServingRuntime"""
        formats = item.get("spec", {}).get("supportedModelFormats", [])
        if formats:
            return formats[0].get("name", "unknown").lower()
        return "unknown"
    
    def _get_predictor_for_framework(self, framework: str, model_uri: str, resources: Dict[str, str], replicas: int, serviceAccountName: Optional[str] = None) -> Dict[str, Any]:
        """Create predictor spec based on framework"""
        resource_limits = {}
        resource_requests = {}
        
        # Set CPU and memory resources
        if "cpu" in resources:
            resource_limits["cpu"] = resources["cpu"]
            resource_requests["cpu"] = resources["cpu"]
            
        if "memory" in resources:
            resource_limits["memory"] = resources["memory"]
            resource_requests["memory"] = resources["memory"]
        
        # Add GPU if specified
        if "gpu" in resources and resources["gpu"]:
            resource_limits["nvidia.com/gpu"] = resources["gpu"]
        
        # Build resources object
        resources_obj = {
            "limits": resource_limits,
            "requests": resource_requests
        }
        
        # Create predictor object
        predictor = {
            "minReplicas": replicas
        }
        
        # Add serviceAccountName if provided
        if serviceAccountName:
            predictor["serviceAccountName"] = serviceAccountName
            
        # Handle MLflow separately as it uses a different structure
        if framework == "mlflow":
            predictor["model"] = {
                "modelFormat": {
                    "name": "mlflow"
                },
                "protocolVersion": "v2",
                "storageUri": model_uri,
                "resources": resources_obj
            }
        else:
            # Create framework-specific predictor for other frameworks
            predictor[framework] = {
                "storageUri": model_uri,
                "resources": resources_obj
            }
        
        return predictor 

    def _extract_service_account(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract serviceAccountName from InferenceService"""
        predictor = item.get("spec", {}).get("predictor", {})
        return predictor.get("serviceAccountName")

    def get_pod_details(self, name: str, namespace="default") -> List[Dict[str, Any]]:
        """Get pod details for a specific InferenceService
        
        Args:
            name: Name of the InferenceService
            namespace: Kubernetes namespace
            
        Returns:
            List of pod details
        """
        try:
            # Lọc các pod theo label của KServe
            label_selector = f"serving.kserve.io/inferenceservice={name}"
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            results = []
            for pod in pods.items:
                # Lấy thông tin container
                containers = []
                for container in pod.spec.containers:
                    container_info = {
                        "name": container.name,
                        "image": container.image,
                        "resources": {
                            "requests": container.resources.requests if container.resources.requests else {},
                            "limits": container.resources.limits if container.resources.limits else {}
                        }
                    }
                    containers.append(container_info)
                
                # Lấy thông tin pod metrics
                try:
                    metrics_info = {}
                    metrics_api = client.CustomObjectsApi()
                    metrics = metrics_api.get_namespaced_custom_object(
                        group="metrics.k8s.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="pods",
                        name=pod.metadata.name
                    )
                    if metrics and "containers" in metrics:
                        for container_metrics in metrics["containers"]:
                            metrics_info[container_metrics["name"]] = {
                                "cpu": container_metrics.get("usage", {}).get("cpu", "unknown"),
                                "memory": container_metrics.get("usage", {}).get("memory", "unknown")
                            }
                except:
                    # Metrics API might not be available
                    metrics_info = {"error": "Metrics API not available"}
                
                # Thông tin pod
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name,
                    "start_time": pod.status.start_time.isoformat() if pod.status.start_time else None,
                    "containers": containers,
                    "metrics": metrics_info,
                    "labels": pod.metadata.labels,
                    "restart_count": sum(container_status.restart_count for container_status in pod.status.container_statuses) if pod.status.container_statuses else 0
                }
                results.append(pod_info)
            
            return results
        except Exception as e:
            logger.error(f"Error getting pod details for {name} in namespace {namespace}: {str(e)}")
            return []

    def get_all_pods(self, namespace="bankchurn-kserve-2") -> List[Dict[str, Any]]:
        """Get all pods in a specific namespace
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            List of pod details
        """
        try:
            pods = self.core_api.list_namespaced_pod(namespace=namespace)
            
            results = []
            for pod in pods.items:
                # Xác định loại pod (InferenceService, MLflow, hoặc khác)
                pod_type = "Other"
                if pod.metadata.labels and "serving.kserve.io/inferenceservice" in pod.metadata.labels:
                    pod_type = "InferenceService"
                    inference_service_name = pod.metadata.labels["serving.kserve.io/inferenceservice"]
                elif pod.metadata.name.startswith("mlflow-"):
                    pod_type = "MLflow"
                
                # Thông tin cơ bản về pod
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "type": pod_type,
                    "phase": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name,
                    "start_time": pod.status.start_time.isoformat() if pod.status.start_time else None,
                    "labels": pod.metadata.labels,
                    "containers": [container.name for container in pod.spec.containers],
                    "ready": all(status.ready for status in pod.status.container_statuses) if pod.status.container_statuses else False,
                    "restart_count": sum(container_status.restart_count for container_status in pod.status.container_statuses) if pod.status.container_statuses else 0
                }
                
                # Thêm tên InferenceService nếu là pod của KServe
                if pod_type == "InferenceService" and inference_service_name:
                    pod_info["inference_service"] = inference_service_name
                
                results.append(pod_info)
            
            return results
        except Exception as e:
            logger.error(f"Error getting all pods in namespace {namespace}: {str(e)}")
            return [] 