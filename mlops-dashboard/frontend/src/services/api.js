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
  getMockExperiments: () => api.get('/mlflow/mock/experiments'),
  getMockRuns: () => api.get('/mlflow/mock/runs'),
  getMockModels: () => api.get('/mlflow/mock/models'),
  
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
  getMockPipelines: () => api.get('/kubeflow/mock/pipelines'),
  getMockRuns: () => api.get('/kubeflow/mock/runs'),
  getMockPipelineGraph: (pipelineId) => api.get(`/kubeflow/mock/pipeline-graph?pipeline_id=${pipelineId}`),
};

// KServe API calls
export const kserveApi = {
  getDeployments: (namespace) => api.get('/kserve/deployments', { params: { namespace } }),
  getDeployment: (name, namespace = 'default') => api.get(`/kserve/deployments/${name}`, { params: { namespace } }),
  createDeployment: (data) => api.post('/kserve/deployments', data),
  deleteDeployment: (name, namespace = 'default') => api.delete(`/kserve/deployments/${name}`, { params: { namespace } }),
  getServingRuntimes: (namespace) => api.get('/kserve/serving-runtimes', { params: { namespace } }),
  getLogs: (name, namespace = 'default') => api.get(`/kserve/deployments/${name}/logs`, { params: { namespace } }),
  getPods: (namespace = 'bankchurn-kserve-2') => api.get(`/kserve/pods`, { params: { namespace } }),
  getDeploymentPods: (name, namespace = 'default') => 
    api.get(`/kserve/deployments/${name}/pods`, { params: { namespace } }),
  
  // Mock API calls
  getMockDeployments: () => api.get('/kserve/mock/deployments'),
  getMockServingRuntimes: () => api.get('/kserve/mock/serving-runtimes'),
};

export default api; 