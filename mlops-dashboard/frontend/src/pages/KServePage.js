import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  CardHeader,
  Divider,
  Button,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  Tab,
  Tabs,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Switch,
  FormControlLabel
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PublishIcon from '@mui/icons-material/Publish';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import { useMockMode } from '../context/MockModeContext';
import { kserveApi } from '../services/api';

const KServePage = () => {
  const { mockMode, setMockMode } = useMockMode();
  const [tabValue, setTabValue] = useState(0);
  const [deployments, setDeployments] = useState([]);
  const [servingRuntimes, setServingRuntimes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [logDialog, setLogDialog] = useState(false);
  const [selectedDeployment, setSelectedDeployment] = useState(null);
  const [logs, setLogs] = useState([]);
  const [pods, setPods] = useState([]);
  const [podsLoading, setPodsLoading] = useState(false);
  
  // Framework options
  const frameworks = [
    { value: 'tensorflow', label: 'TensorFlow' },
    { value: 'pytorch', label: 'PyTorch' },
    { value: 'sklearn', label: 'Scikit-Learn' },
    { value: 'xgboost', label: 'XGBoost' },
    { value: 'onnx', label: 'ONNX' },
    { value: 'mlflow', label: 'MLflow' }
  ];
  
  // Form state
  const [form, setForm] = useState({
    name: '',
    namespace: 'default',
    model_uri: '',
    framework: 'tensorflow',
    replicas: 1,
    serviceAccountName: '',
    resources: {
      cpu: '1',
      memory: '2Gi'
    }
  });
  
  // Toggle mock mode handler
  const handleToggleMockMode = () => {
    setMockMode(!mockMode);
  };

  // Handle form change
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setForm({
        ...form,
        [parent]: {
          ...form[parent],
          [child]: value
        }
      });
    } else {
      setForm({
        ...form,
        [name]: value
      });
    }
  };
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Xử lý khi chọn một deployment
  const handleSelectDeployment = (deployment) => {
    setSelectedDeployment(deployment);
  };

  // Load deployments data
  const loadDeployments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      if (mockMode) {
        response = await kserveApi.getMockDeployments();
      } else {
        response = await kserveApi.getDeployments();
      }
      
      const deploymentList = response.data.deployments;
      setDeployments(deploymentList);
      
      // Chọn deployment đầu tiên nếu có và chưa có deployment nào được chọn
      if (deploymentList.length > 0 && !selectedDeployment) {
        setSelectedDeployment(deploymentList[0]);
      } else if (selectedDeployment) {
        // Cập nhật thông tin của deployment đã chọn nếu vẫn tồn tại
        const updated = deploymentList.find(d => d.name === selectedDeployment.name && d.namespace === selectedDeployment.namespace);
        if (updated) {
          setSelectedDeployment(updated);
        } else if (deploymentList.length > 0) {
          // Nếu deployment đã chọn không còn tồn tại, chọn deployment đầu tiên
          setSelectedDeployment(deploymentList[0]);
        } else {
          setSelectedDeployment(null);
        }
      }
    } catch (error) {
      console.error('Error loading deployments:', error);
      setError('Failed to load deployments. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Load serving runtimes data
  const loadServingRuntimes = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      if (mockMode) {
        response = await kserveApi.getMockServingRuntimes();
      } else {
        response = await kserveApi.getServingRuntimes();
      }
      
      setServingRuntimes(response.data.runtimes);
    } catch (error) {
      console.error('Error loading serving runtimes:', error);
      setError('Failed to load serving runtimes. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Load all pods
  const loadPods = async () => {
    if (mockMode) return; // Skip in mock mode
    
    setPodsLoading(true);
    try {
      const response = await kserveApi.getPods();
      setPods(response.data.pods);
    } catch (error) {
      console.error('Error loading pods:', error);
    } finally {
      setPodsLoading(false);
    }
  };
  
  // Create deployment
  const handleCreateDeployment = async () => {
    setError(null);
    
    try {
      if (mockMode) {
        // Simulate deployment creation in mock mode
        const newDeployment = {
          ...form,
          created: new Date().toISOString(),
          status: 'Creating',
          endpoint: `http://${form.name}.${form.namespace}.example.com/v1/models/${form.name}`,
          traffic: 100,
          version: '1'
        };
        
        setDeployments([newDeployment, ...deployments]);
        
        // Simulate status change
        setTimeout(() => {
          setDeployments(prevDeployments => 
            prevDeployments.map(d => 
              d.name === form.name ? { ...d, status: 'Running' } : d
            )
          );
        }, 3000);
      } else {
        // Create actual deployment
        await kserveApi.createDeployment(form);
        await loadDeployments();  // Refresh the list
      }
      
      // Close dialog and reset form
      setOpenDialog(false);
      setForm({
        name: '',
        namespace: 'default',
        model_uri: '',
        framework: 'tensorflow',
        replicas: 1,
        serviceAccountName: '',
        resources: {
          cpu: '1',
          memory: '2Gi'
        }
      });
    } catch (error) {
      console.error('Error creating deployment:', error);
      setError('Failed to create deployment. Please check the form and try again.');
    }
  };
  
  // Delete deployment
  const handleDeleteDeployment = async (name, namespace = 'default') => {
    setError(null);
    
    try {
      if (mockMode) {
        // Simulate deletion in mock mode
        setDeployments(deployments.filter(d => d.name !== name));
      } else {
        // Delete actual deployment
        await kserveApi.deleteDeployment(name);
        await loadDeployments();  // Refresh the list
      }
    } catch (error) {
      console.error('Error deleting deployment:', error);
      setError('Failed to delete deployment. Please try again.');
    }
  };
  
  // View logs
  const handleViewLogs = async (deployment) => {
    setSelectedDeployment(deployment);
    setLogDialog(true);
    setLogs([]);
    
    try {
      if (!mockMode) {
        const response = await kserveApi.getLogs(deployment.name, deployment.namespace);
        setLogs(response.data.logs);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
      setLogs(['Error fetching logs: ' + error.message]);
    }
  };
  
  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };
  
  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'Running':
        return 'success';
      case 'Creating':
        return 'info';
      case 'Failed':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Initialize data on component mount, setting mockMode to false
  useEffect(() => {
    // Đặt mockMode thành false khi component mount
    setMockMode(false);
    
    // Sau đó tải dữ liệu
    const fetchData = async () => {
      if (tabValue === 0) {
        await loadDeployments();
        if (!mockMode) {
          await loadPods();
        }
      } else {
        await loadServingRuntimes();
      }
    };
    
    fetchData();
  }, []);

  // Refresh data handler
  const handleRefresh = () => {
    if (tabValue === 0) {
      loadDeployments();
      if (!mockMode) {
        loadPods();
      }
    } else {
      loadServingRuntimes();
    }
  };

  // Load data when tabValue or mockMode changes
  useEffect(() => {
    const fetchData = async () => {
      if (tabValue === 0) {
        await loadDeployments();
        if (!mockMode) {
          await loadPods();
        }
      } else {
        await loadServingRuntimes();
      }
    };
    
    fetchData();
  }, [tabValue, mockMode]);

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h2" gutterBottom>
          KServe
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body1">
            Quản lý và triển khai các mô hình ML sử dụng KServe.
          </Typography>
          <FormControlLabel
            control={<Switch checked={mockMode} onChange={handleToggleMockMode} color="primary" />}
            label="Chế độ mô phỏng"
            labelPlacement="start"
          />
        </Box>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Grid>
      
      {/* Tabs */}
      <Grid item xs={12}>
        <Card>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="kserve tabs">
              <Tab label="Deployments" />
              <Tab label="Serving Runtimes" />
            </Tabs>
          </Box>
          
          {/* Deployments Tab */}
          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={() => setOpenDialog(true)}
                >
                  Deploy Model
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => {
                    setForm({
                      name: "bankchurn",
                      namespace: "bankchurn-kserve-2",
                      model_uri: "s3://mlflow-artifacts/3/3cad7a3d97dc44c4a07ef03680442b79/artifacts/model/",
                      framework: "mlflow",
                      replicas: 1,
                      serviceAccountName: "sa-minio-kserve",
                      resources: {
                        cpu: "1",
                        memory: "2Gi"
                      }
                    });
                    setOpenDialog(true);
                  }}
                >
                  Bank Churn Template
                </Button>
              </Box>
              <Tooltip title="Refresh">
                <IconButton onClick={handleRefresh}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
                {deployments.length > 0 ? (
                  <Table sx={{ minWidth: 650 }}>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Framework</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Replicas</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {deployments.map((deployment) => (
                        <TableRow 
                          key={deployment.name} 
                          hover
                          onClick={() => handleSelectDeployment(deployment)}
                          selected={selectedDeployment && selectedDeployment.name === deployment.name && selectedDeployment.namespace === deployment.namespace}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                              <Typography variant="body2" fontWeight="bold">
                                {deployment.name}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                Namespace: {deployment.namespace}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={deployment.framework} 
                              size="small" 
                              color="primary"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={deployment.status} 
                              size="small" 
                              color={getStatusColor(deployment.status)}
                            />
                            {deployment.error && (
                              <Typography variant="caption" color="error" display="block">
                                {deployment.error}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>{deployment.replicas}</TableCell>
                          <TableCell>{formatDate(deployment.created)}</TableCell>
                          <TableCell>
                            <Tooltip title="View Logs">
                              <IconButton size="small" onClick={() => handleViewLogs(deployment)}>
                                <VisibilityIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Edit">
                              <IconButton size="small">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => handleDeleteDeployment(deployment.name, deployment.namespace)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="body1" color="textSecondary">
                      {mockMode ? 
                        "Không tìm thấy dữ liệu mô phỏng. Vui lòng thử làm mới trang." : 
                        "Không tìm thấy model nào được triển khai trên KServe. Hãy tạo model mới hoặc kiểm tra cấu hình của bạn."
                      }
                    </Typography>
                    {!mockMode && (
                      <Alert severity="info" sx={{ mt: 2, textAlign: 'left' }}>
                        <Typography variant="body2">
                          Nếu bạn đang kiểm tra giao diện hoặc chưa cài đặt KServe, bạn có thể bật "Chế độ mô phỏng" để xem dữ liệu mẫu.
                        </Typography>
                      </Alert>
                    )}
                  </Box>
                )}
              </TableContainer>
            )}
          </TabPanel>
          
          {/* Serving Runtimes Tab */}
          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <Tooltip title="Refresh">
                <IconButton onClick={handleRefresh}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
            
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
                {servingRuntimes.length > 0 ? (
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Framework</TableCell>
                        <TableCell>Version</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Scope</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {servingRuntimes.map((runtime) => (
                        <TableRow key={runtime.name + (runtime.namespace || '')}>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                              <Typography variant="body2" fontWeight="bold">
                                {runtime.name}
                              </Typography>
                              {runtime.namespace && (
                                <Typography variant="caption" color="textSecondary">
                                  Namespace: {runtime.namespace}
                                </Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={runtime.framework} 
                              size="small" 
                              color="primary"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{runtime.version}</TableCell>
                          <TableCell>
                            <Chip 
                              label={runtime.status} 
                              size="small" 
                              color={runtime.status === 'Available' ? 'success' : 'error'}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={runtime.scope} 
                              size="small" 
                              color={
                                runtime.scope === 'Cluster' ? 'info' : 
                                runtime.scope === 'Namespaced' ? 'secondary' : 
                                'default'
                              }
                              variant="outlined"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="body1" color="textSecondary">
                      {mockMode ? 
                        "Không tìm thấy dữ liệu mô phỏng về Serving Runtimes. Vui lòng thử làm mới trang." : 
                        "Không tìm thấy Serving Runtime nào trên hệ thống KServe."
                      }
                    </Typography>
                    {!mockMode && (
                      <Alert severity="info" sx={{ mt: 2, textAlign: 'left' }}>
                        <Typography variant="body2">
                          Serving Runtime là các thành phần của KServe để triển khai model. Hệ thống không tìm thấy runtime nào được cài đặt trong cụm Kubernetes. KServe sử dụng runtime mặc định được tích hợp sẵn khi không có runtime cụ thể nào được định nghĩa.
                        </Typography>
                      </Alert>
                    )}
                  </Box>
                )}
              </TableContainer>
            )}
          </TabPanel>
        </Card>
      </Grid>
      
      {/* Selected Deployment Details */}
      {tabValue === 0 && selectedDeployment && (
        <Grid item xs={12}>
          <Card>
            <CardHeader 
              title={`Deployment Details: ${selectedDeployment.name}`}
              titleTypographyProps={{ variant: 'h6' }}
              subheader={`Namespace: ${selectedDeployment.namespace}`}
            />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Model Information
                      </Typography>
                      <Typography variant="body2">
                        <strong>Name:</strong> {selectedDeployment.name}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Framework:</strong> {selectedDeployment.framework}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Version:</strong> {selectedDeployment.version}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Model URI:</strong> {selectedDeployment.model_uri}
                      </Typography>
                      {selectedDeployment.serviceAccountName && (
                        <Typography variant="body2">
                          <strong>Service Account:</strong> {selectedDeployment.serviceAccountName}
                        </Typography>
                      )}
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Runtime Configuration
                      </Typography>
                      <Typography variant="body2">
                        <strong>Replicas:</strong> {selectedDeployment.replicas}
                      </Typography>
                      <Typography variant="body2">
                        <strong>CPU:</strong> {selectedDeployment.resources?.cpu || "N/A"}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Memory:</strong> {selectedDeployment.resources?.memory || "N/A"}
                      </Typography>
                      {selectedDeployment.resources?.gpu && (
                        <Typography variant="body2">
                          <strong>GPU:</strong> {selectedDeployment.resources.gpu}
                        </Typography>
                      )}
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Endpoint Information
                      </Typography>
                      <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                        <strong>Endpoint URL:</strong> {selectedDeployment.endpoint}
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Sample Request
                        </Typography>
                        <Paper 
                          sx={{ 
                            bgcolor: '#f5f5f5', 
                            p: 1.5, 
                            fontFamily: 'monospace',
                            fontSize: '0.875rem',
                            overflowX: 'auto'
                          }}
                        >
                          {selectedDeployment.framework === 'mlflow' ? 
                            `curl -X POST ${selectedDeployment.endpoint}/v2/models/${selectedDeployment.name}/infer \\
  -H "Content-Type: application/json" \\
  -d '{
  "inputs": [
    {"name": "CreditScore", "datatype": "FP64", "shape": [1], "data": [619]},
    {"name": "Geography", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "Gender", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "Age", "datatype": "FP64", "shape": [1], "data": [42]},
    {"name": "Tenure", "datatype": "FP64", "shape": [1], "data": [2]},
    {"name": "Balance", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "NumOfProducts", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "HasCrCard", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "IsActiveMember", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "EstimatedSalary", "datatype": "FP64", "shape": [1], "data": [101348.88]}
  ]
}'` :
                            `curl -X POST ${selectedDeployment.endpoint}/predict \\
  -H "Content-Type: application/json" \\
  -d '{"instances": [...input data...]}'`}
                        </Paper>
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )}
      
      {/* Pod Information */}
      {tabValue === 0 && !mockMode && (
        <Grid item xs={12}>
          <Card>
            <CardHeader 
              title="Pod Information" 
              titleTypographyProps={{ variant: 'h6' }}
              action={
                <Tooltip title="Refresh Pods">
                  <IconButton onClick={loadPods} disabled={podsLoading}>
                    {podsLoading ? <CircularProgress size={24} /> : <RefreshIcon />}
                  </IconButton>
                </Tooltip>
              }
            />
            <Divider />
            <CardContent>
              {podsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : pods.length > 0 ? (
                <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Pod Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Restarts</TableCell>
                        <TableCell>Started</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {pods.map((pod) => (
                        <TableRow key={pod.name}>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                              <Typography variant="body2" fontWeight="bold">
                                {pod.name}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                Namespace: {pod.namespace}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={pod.type} 
                              size="small" 
                              color={pod.type === "InferenceService" ? "primary" : "secondary"}
                              variant="outlined"
                            />
                            {pod.type === "InferenceService" && pod.inference_service && (
                              <Typography variant="caption" display="block">
                                Service: {pod.inference_service}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={pod.phase} 
                              size="small" 
                              color={pod.phase === "Running" ? "success" : 
                                     pod.phase === "Pending" ? "warning" : "error"}
                            />
                          </TableCell>
                          <TableCell>{pod.restart_count}</TableCell>
                          <TableCell>
                            {pod.start_time ? new Date(pod.start_time).toLocaleString() : "N/A"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="body1" color="textSecondary">
                    Không tìm thấy pod nào trong namespace bankchurn-kserve-2.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      )}
      
      {/* Deploy Model Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Deploy Model</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Name"
                name="name"
                value={form.name}
                onChange={handleFormChange}
                fullWidth
                margin="normal"
                required
                placeholder="bankchurn"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Namespace"
                name="namespace"
                value={form.namespace}
                onChange={handleFormChange}
                fullWidth
                margin="normal"
                required
                placeholder="bankchurn-kserve-2"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Model URI"
                name="model_uri"
                value={form.model_uri}
                onChange={handleFormChange}
                fullWidth
                margin="normal"
                required
                placeholder="s3://mlflow-artifacts/3/3cad7a3d97dc44c4a07ef03680442b79/artifacts/model/"
                helperText="S3, GCS, or HTTP URI pointing to your model"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="framework-label">Framework</InputLabel>
                <Select
                  labelId="framework-label"
                  id="framework"
                  name="framework"
                  value={form.framework}
                  label="Framework"
                  onChange={handleFormChange}
                >
                  {frameworks.map((framework) => (
                    <MenuItem key={framework.value} value={framework.value}>{framework.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Replicas"
                name="replicas"
                type="number"
                value={form.replicas}
                onChange={handleFormChange}
                fullWidth
                margin="normal"
                required
                inputProps={{ min: 1 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="CPU"
                name="resources.cpu"
                value={form.resources.cpu}
                onChange={handleFormChange}
                fullWidth
                margin="normal"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Memory"
                name="resources.memory"
                value={form.resources.memory}
                onChange={handleFormChange}
                fullWidth
                margin="normal"
                required
                placeholder="2Gi"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="service-account-label">Service Account</InputLabel>
                <TextField
                  label="Service Account"
                  name="serviceAccountName"
                  value={form.serviceAccountName || ""}
                  onChange={handleFormChange}
                  fullWidth
                  placeholder="sa-minio-kserve"
                  helperText="Service account for model access credentials"
                />
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                Sample Input Format
              </Typography>
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <pre style={{ margin: 0, overflow: 'auto', fontSize: '0.85rem' }}>
{`{
  "inputs": [
    {"name": "CreditScore", "datatype": "FP64", "shape": [1], "data": [619]},
    {"name": "Geography", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "Gender", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "Age", "datatype": "FP64", "shape": [1], "data": [42]},
    {"name": "Tenure", "datatype": "FP64", "shape": [1], "data": [2]},
    {"name": "Balance", "datatype": "FP64", "shape": [1], "data": [0]},
    {"name": "NumOfProducts", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "HasCrCard", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "IsActiveMember", "datatype": "FP64", "shape": [1], "data": [1]},
    {"name": "EstimatedSalary", "datatype": "FP64", "shape": [1], "data": [101348.88]}
  ]
}`}
                </pre>
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateDeployment} 
            variant="contained" 
            color="primary"
            startIcon={<PublishIcon />}
            disabled={!form.name || !form.model_uri}
          >
            Deploy
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Logs Dialog */}
      <Dialog 
        open={logDialog} 
        onClose={() => setLogDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          {selectedDeployment ? `Logs: ${selectedDeployment.name}` : 'Logs'}
        </DialogTitle>
        <DialogContent>
          <Paper 
            sx={{ 
              bgcolor: '#000', 
              color: '#00ff00', 
              p: 2, 
              height: 300, 
              overflow: 'auto',
              fontFamily: 'monospace'
            }}
          >
            {mockMode ? (
              selectedDeployment?.status === 'Running' ? (
                <>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:31:15] INFO: Starting model server for {selectedDeployment?.framework}
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:31:16] INFO: Loading model from {selectedDeployment?.model_uri}
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:31:20] INFO: Model loaded successfully
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:31:21] INFO: Starting HTTP server at port 8080
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:31:22] INFO: Server started successfully
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:35:45] INFO: Received inference request
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:35:45] INFO: Processing batch of 10 instances
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-05-01 10:35:46] INFO: Request processed successfully (0.254s)
                  </Typography>
                </>
              ) : selectedDeployment?.status === 'Failed' ? (
                <>
                  <Typography variant="body2" component="div">
                    [2023-04-01 14:11:15] INFO: Starting model server for {selectedDeployment?.framework}
                  </Typography>
                  <Typography variant="body2" component="div">
                    [2023-04-01 14:11:16] INFO: Loading model from {selectedDeployment?.model_uri}
                  </Typography>
                  <Typography variant="body2" component="div" sx={{ color: '#ff6b6b' }}>
                    [2023-04-01 14:11:30] ERROR: Failed to allocate resources: {selectedDeployment?.error}
                  </Typography>
                  <Typography variant="body2" component="div" sx={{ color: '#ff6b6b' }}>
                    [2023-04-01 14:11:31] ERROR: Container startup failed
                  </Typography>
                  <Typography variant="body2" component="div" sx={{ color: '#ff6b6b' }}>
                    [2023-04-01 14:11:32] ERROR: Deployment failed with status code 500
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" component="div">
                  No logs available.
                </Typography>
              )
            ) : (
              logs.length > 0 ? (
                logs.map((log, index) => (
                  <Typography key={index} variant="body2" component="div">
                    {log}
                  </Typography>
                ))
              ) : (
                <Typography variant="body2" component="div">
                  Loading logs...
                </Typography>
              )
            )}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

// Tab Panel component
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`kserve-tabpanel-${index}`}
      aria-labelledby={`kserve-tab-${index}`}
      {...other}
      style={{ padding: '16px' }}
    >
      {value === index && children}
    </div>
  );
}

export default KServePage; 