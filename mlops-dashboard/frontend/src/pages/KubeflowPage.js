import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  CardHeader,
  Divider,
  Button,
  TextField,
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
  Chip
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { kubeflowApi } from '../services/api';
import { useMockMode } from '../context/MockModeContext';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  Handle, 
  Position,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom Node component for pipeline visualization
const PipelineNode = ({ data }) => {
  const getStatusClass = (status) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'node-completed';
      case 'running':
        return 'node-running';
      case 'failed':
        return 'node-failed';
      default:
        return 'node-waiting';
    }
  };
  
  return (
    <div className={`pipeline-node ${getStatusClass(data.status)}`}>
      <Handle type="target" position={Position.Left} />
      <div>
        <Typography variant="subtitle2">{data.name}</Typography>
        <Typography variant="caption">{data.type}</Typography>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

const nodeTypes = {
  pipelineNode: PipelineNode,
};

const KubeflowPage = () => {
  const { mockMode } = useMockMode();
  const [tabValue, setTabValue] = useState(0);
  const [kubeflowStatus, setKubeflowStatus] = useState('stopped');
  const [kubeflowUrl, setKubeflowUrl] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);
  const [pipelines, setPipelines] = useState([]);
  const [runs, setRuns] = useState([]);
  const [pipelineGraph, setPipelineGraph] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Configuration state
  const [config, setConfig] = useState({
    port: 8080,
    namespace: 'kubeflow',
    service: 'ml-pipeline-ui'
  });
  
  // Command for port-forward
  const [portForwardCommand, setPortForwardCommand] = useState('');
  
  // Handle config change
  const handleConfigChange = (e) => {
    setConfig({
      ...config,
      [e.target.name]: e.target.value
    });
  };
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Get port-forward command
  const getPortForwardCommand = async () => {
    try {
      const response = await kubeflowApi.getPortForwardCommand(config);
      setPortForwardCommand(response.data.command);
    } catch (error) {
      console.error('Error getting port-forward command:', error);
      setError('Failed to generate port-forward command.');
    }
  };
  
  // Copy command to clipboard
  const copyToClipboard = () => {
    navigator.clipboard.writeText(portForwardCommand);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };
  
  // Check Kubeflow connection
  const checkConnection = async () => {
    setLoading(true);
    
    if (!mockMode) {
      try {
        const response = await kubeflowApi.checkConnection(config.port);
        if (response.data.connected) {
          setKubeflowStatus('running');
          setKubeflowUrl(response.data.url);
        } else {
          setKubeflowStatus('stopped');
          setError(`Connection failed: ${response.data.error}`);
        }
      } catch (error) {
        console.error('Error checking Kubeflow connection:', error);
        setKubeflowStatus('stopped');
        setError('Failed to check Kubeflow connection.');
      }
    } else {
      // Simulate in mock mode
      setKubeflowStatus('running');
      setKubeflowUrl(`http://localhost:${config.port}`);
    }
    
    setLoading(false);
  };
  
  // Disconnect (simulated)
  const disconnect = () => {
    setKubeflowStatus('stopped');
    setKubeflowUrl('');
  };
  
  // Open Kubeflow UI in new tab
  const openKubeflowUi = () => {
    window.open(kubeflowUrl, '_blank');
  };
  
  // Fetch mock data
  const fetchMockData = async () => {
    try {
      setLoading(true);
      
      const pipelinesRes = await kubeflowApi.getMockPipelines();
      setPipelines(pipelinesRes.data.pipelines);
      
      const runsRes = await kubeflowApi.getMockRuns();
      setRuns(runsRes.data.runs);
      
      const graphRes = await kubeflowApi.getMockPipelineGraph();
      
      // Transform graph data for ReactFlow
      const nodes = graphRes.data.nodes.map((node) => ({
        id: node.id,
        type: 'pipelineNode',
        data: {
          name: node.name,
          type: node.type,
          status: node.status
        },
        position: { 
          x: graphRes.data.nodes.indexOf(node) * 250, 
          y: 100 
        },
      }));
      
      const edges = graphRes.data.edges.map((edge) => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
      }));
      
      setPipelineGraph({ nodes, edges });
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching mock data:', error);
      setError('Failed to load data. Please try again.');
      setLoading(false);
    }
  };
  
  // Load data on component mount
  useEffect(() => {
    fetchMockData();
    getPortForwardCommand();
    
    if (mockMode) {
      // Set mock data in mock mode
      setKubeflowStatus('stopped');
    }
  }, [mockMode, config]);
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h2" gutterBottom>
          Kubeflow Pipelines
        </Typography>
        <Typography variant="body1" paragraph>
          Quản lý và theo dõi Kubeflow Pipelines.
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {copySuccess && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setCopySuccess(false)}>
            Đã sao chép lệnh vào clipboard!
          </Alert>
        )}
      </Grid>
      
      {/* Connection Control */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader 
            title="Kết nối Kubeflow" 
            titleTypographyProps={{ variant: 'h6' }}
            action={
              <Tooltip title="Làm mới trạng thái">
                <IconButton onClick={checkConnection} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            }
          />
          <Divider />
          <CardContent>
            <Typography variant="body1" gutterBottom>
              Trạng thái: 
              <span className={`status-${kubeflowStatus}`} style={{ marginLeft: '8px' }}>
                {kubeflowStatus === 'running' ? 'Đã kết nối' : 'Chưa kết nối'}
              </span>
            </Typography>
            
            {kubeflowStatus === 'running' && (
              <Box sx={{ mt: 2, mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Kubeflow UI đang chạy tại:
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography 
                    variant="body2" 
                    component="a" 
                    href={kubeflowUrl} 
                    target="_blank"
                    sx={{ color: 'primary.main', textDecoration: 'none', mr: 1 }}
                  >
                    {kubeflowUrl}
                  </Typography>
                  <IconButton size="small" color="primary" onClick={openKubeflowUi}>
                    <OpenInNewIcon fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
            )}
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Cấu hình Kết nối
            </Typography>
            
            <TextField
              label="Port"
              name="port"
              type="number"
              value={config.port}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              size="small"
            />
            
            <TextField
              label="Namespace"
              name="namespace"
              value={config.namespace}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              size="small"
            />
            
            <TextField
              label="Service"
              name="service"
              value={config.service}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              size="small"
            />
            
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Port-forward Command:
            </Typography>
            
            <Paper variant="outlined" sx={{ p: 1, bgcolor: '#f5f5f5' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', flexGrow: 1, overflow: 'auto' }}>
                  {portForwardCommand}
                </Typography>
                <IconButton size="small" onClick={copyToClipboard}>
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Box>
            </Paper>
            <Typography variant="caption" color="textSecondary">
              Chạy lệnh này trong terminal để port-forward service.
            </Typography>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              {kubeflowStatus !== 'running' ? (
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={checkConnection}
                  disabled={loading}
                  sx={{ minWidth: '180px' }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Kiểm tra kết nối'}
                </Button>
              ) : (
                <Button 
                  variant="contained" 
                  color="error" 
                  onClick={disconnect}
                  disabled={loading}
                  sx={{ minWidth: '180px' }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Ngắt kết nối'}
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      {/* Data Tabs */}
      <Grid item xs={12} md={8}>
        <Card>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="kubeflow data tabs">
              <Tab label="Pipelines" />
              <Tab label="Runs" />
              <Tab label="Visualization" />
            </Tabs>
          </Box>
          
          {/* Pipelines Tab */}
          <TabPanel value={tabValue} index={0}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List sx={{ width: '100%' }}>
                {pipelines.map((pipeline) => (
                  <React.Fragment key={pipeline.id}>
                    <ListItem>
                      <ListItemText
                        primary={pipeline.name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              ID: {pipeline.id}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Description: {pipeline.description}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Created: {new Date(pipeline.created_at).toLocaleString()}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            )}
          </TabPanel>
          
          {/* Runs Tab */}
          <TabPanel value={tabValue} index={1}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List sx={{ width: '100%' }}>
                {runs.map((run, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemText
                        primary={run.run_name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              Pipeline: {pipelines.find(p => p.id === run.pipeline_id)?.name || run.pipeline_id}
                            </Typography>
                            <br />
                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5, mb: 0.5 }}>
                              <Chip 
                                label={run.status} 
                                size="small" 
                                color={
                                  run.status === 'Completed' ? 'success' : 
                                  run.status === 'Running' ? 'info' : 
                                  run.status === 'Failed' ? 'error' : 'default'
                                }
                                sx={{ mr: 1 }}
                              />
                              <Typography component="span" variant="caption">
                                Duration: {run.duration}
                              </Typography>
                            </Box>
                            <Typography component="span" variant="body2">
                              Start: {new Date(run.start_time).toLocaleString()}
                            </Typography>
                            {run.end_time && (
                              <>
                                <br />
                                <Typography component="span" variant="body2">
                                  End: {new Date(run.end_time).toLocaleString()}
                                </Typography>
                              </>
                            )}
                            {run.error && (
                              <>
                                <br />
                                <Typography component="span" variant="body2" color="error">
                                  Error: {run.error}
                                </Typography>
                              </>
                            )}
                          </>
                        }
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            )}
          </TabPanel>
          
          {/* Visualization Tab */}
          <TabPanel value={tabValue} index={2}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Box sx={{ height: 400 }}>
                <ReactFlow
                  nodes={pipelineGraph.nodes}
                  edges={pipelineGraph.edges}
                  nodeTypes={nodeTypes}
                  fitView
                >
                  <Background />
                  <Controls />
                  <MiniMap />
                </ReactFlow>
              </Box>
            )}
          </TabPanel>
        </Card>
      </Grid>
      
      {/* Additional Info */}
      <Grid item xs={12}>
        <Card>
          <CardHeader 
            title="Thông tin Kubeflow Pipelines" 
            titleTypographyProps={{ variant: 'h6' }}
          />
          <Divider />
          <CardContent>
            <Typography variant="body2" paragraph>
              Kubeflow Pipelines là một nền tảng để xây dựng và triển khai các workflow ML có thể mở rộng và di động. Các tính năng chính bao gồm:
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Paper elevation={0} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Pipelines
                  </Typography>
                  <Typography variant="body2">
                    Define và chạy end-to-end ML workflows với các components khả tái sử dụng.
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper elevation={0} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Experiments
                  </Typography>
                  <Typography variant="body2">
                    Tổ chức pipeline runs thành các nhóm thí nghiệm ML.
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper elevation={0} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Lên lịch chạy định kỳ
                  </Typography>
                  <Typography variant="body2">
                    Lên lịch pipelines chạy theo thời gian hoặc dựa trên trigger.
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper elevation={0} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Artifacts
                  </Typography>
                  <Typography variant="body2">
                    Theo dõi và quản lý đầu ra của các bước trong pipeline.
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
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
      id={`kubeflow-tabpanel-${index}`}
      aria-labelledby={`kubeflow-tab-${index}`}
      {...other}
      style={{ padding: '16px' }}
    >
      {value === index && children}
    </div>
  );
}

export default KubeflowPage; 