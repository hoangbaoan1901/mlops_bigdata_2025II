import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// MLflow API calls
export const mlflowApi = {
  getStatus: () => api.get('/mlflow/status'),
  startServer: (config) => api.post('/mlflow/start', config),
  stopServer: () => api.post('/mlflow/stop'),
  getLogs: () => api.get('/mlflow/logs'),
  
  // Mock API calls
  getMockExperiments: () => api.get('/mock/mlflow/experiments'),
  getMockRuns: () => api.get('/mock/mlflow/runs'),
  getMockModels: () => api.get('/mock/mlflow/models'),
  
  // Model Registry API calls
  registerModel: (model) => api.post('/mlflow/model-registry/models', model),
  getModelVersions: (modelName) => api.get(`/mlflow/model-registry/models/${modelName}/versions`),
  updateModelVersion: (modelName, version, data) => api.patch(`/mlflow/model-registry/models/${modelName}/versions/${version}`, data),
  deleteModelVersion: (modelName, version) => api.delete(`/mlflow/model-registry/models/${modelName}/versions/${version}`),
};

// Kubeflow API calls
export const kubeflowApi = {
  getPortForwardCommand: (config) => api.get('/kubeflow/port-forward-command', { params: config }),
  checkConnection: (port) => api.get(`/kubeflow/check-connection?port=${port}`),
  
  // Mock API calls
  getMockPipelines: () => api.get('/mock/kubeflow/pipelines'),
  getMockRuns: () => api.get('/mock/kubeflow/runs'),
  getMockPipelineGraph: (pipelineId) => api.get(`/mock/kubeflow/pipeline-graph?pipeline_id=${pipelineId}`),
};

// KServe API calls
export const kserveApi = {
  getDeployments: () => api.get('/kserve/deployments'),
  getDeployment: (name) => api.get(`/kserve/deployments/${name}`),
  createDeployment: (data) => api.post('/kserve/deployments', data),
  updateDeployment: (name, data) => api.put(`/kserve/deployments/${name}`, data),
  deleteDeployment: (name) => api.delete(`/kserve/deployments/${name}`),
  getServingRuntimes: () => api.get('/kserve/serving-runtimes'),
  getLogs: (name) => api.get(`/kserve/deployments/${name}/logs`),
  getPods: (namespace = 'bankchurn-kserve-2') => api.get(`/kserve/pods?namespace=${namespace}`),
  getDeploymentPods: (name, namespace = 'bankchurn-kserve-2') => 
    api.get(`/kserve/deployments/${name}/pods?namespace=${namespace}`),
  
  // Mock API calls
  getMockDeployments: () => api.get('/mock/kserve/deployments'),
  getMockServingRuntimes: () => api.get('/mock/kserve/serving-runtimes'),
};

export default api; 