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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
  CircularProgress
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import RefreshIcon from '@mui/icons-material/Refresh';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { mlflowApi } from '../services/api';
import { useMockMode } from '../context/MockModeContext';

const MLflowPage = () => {
  const { mockMode } = useMockMode();
  const [tabValue, setTabValue] = useState(0);
  const [mlflowStatus, setMlflowStatus] = useState('stopped');
  const [mlflowUrl, setMlflowUrl] = useState('');
  const [logs, setLogs] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [runs, setRuns] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Configuration state
  const [config, setConfig] = useState({
    port: 5000,
    host: '0.0.0.0',
    artifact_uri: './mlruns',
    backend_store_uri: ''
  });
  
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
  
  // Fetch MLflow status
  const fetchStatus = async () => {
    if (!mockMode) {
      try {
        const response = await mlflowApi.getStatus();
        setMlflowStatus(response.data.status);
        if (response.data.url) {
          setMlflowUrl(response.data.url);
        }
      } catch (error) {
        console.error('Error fetching MLflow status:', error);
      }
    }
  };
  
  // Fetch MLflow logs
  const fetchLogs = async () => {
    if (!mockMode) {
      try {
        const response = await mlflowApi.getLogs();
        setLogs(response.data.logs);
      } catch (error) {
        console.error('Error fetching MLflow logs:', error);
      }
    }
  };
  
  // Fetch mock data
  const fetchMockData = async () => {
    try {
      setLoading(true);
      const experimentRes = await mlflowApi.getMockExperiments();
      setExperiments(experimentRes.data.experiments);
      
      const runsRes = await mlflowApi.getMockRuns();
      setRuns(runsRes.data.runs);
      
      const modelsRes = await mlflowApi.getMockModels();
      setModels(modelsRes.data.models);
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching mock data:', error);
      setError('Failed to load data. Please try again.');
      setLoading(false);
    }
  };
  
  // Start MLflow server
  const startServer = async () => {
    if (!mockMode) {
      try {
        setLoading(true);
        const response = await mlflowApi.startServer(config);
        console.log('Server starting:', response.data);
        setMlflowStatus('starting');
        setTimeout(() => {
          fetchStatus();
          fetchLogs();
          setLoading(false);
        }, 2000);
      } catch (error) {
        console.error('Error starting MLflow server:', error);
        setError('Failed to start MLflow server. Please check the configuration.');
        setLoading(false);
      }
    } else {
      // Simulate in mock mode
      setMlflowStatus('running');
      setMlflowUrl(`http://localhost:${config.port}`);
    }
  };
  
  // Stop MLflow server
  const stopServer = async () => {
    if (!mockMode) {
      try {
        setLoading(true);
        const response = await mlflowApi.stopServer();
        console.log('Server stopped:', response.data);
        setMlflowStatus('stopped');
        setLoading(false);
      } catch (error) {
        console.error('Error stopping MLflow server:', error);
        setError('Failed to stop MLflow server.');
        setLoading(false);
      }
    } else {
      // Simulate in mock mode
      setMlflowStatus('stopped');
    }
  };
  
  // Open MLflow UI in new tab
  const openMlflowUi = () => {
    window.open(mlflowUrl, '_blank');
  };
  
  // Load data on component mount
  useEffect(() => {
    fetchMockData();
    
    if (!mockMode) {
      fetchStatus();
      fetchLogs();
    } else {
      // Set mock data for demonstration
      setMlflowStatus('stopped');
      setLogs([
        'INFO mlflow.tracking.fluent: Autologging successfully enabled for tensorflow.',
        'INFO mlflow.tracking.fluent: Autologging successfully enabled for pytorch.'
      ]);
    }
  }, [mockMode]);
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h2" gutterBottom>
          MLflow Management
        </Typography>
        <Typography variant="body1" paragraph>
          Quản lý và theo dõi MLflow server và experiments.
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Grid>
      
      {/* Server Control */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader 
            title="MLflow Server Control" 
            titleTypographyProps={{ variant: 'h6' }}
            action={
              <Tooltip title="Refresh Status">
                <IconButton onClick={fetchStatus} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            }
          />
          <Divider />
          <CardContent>
            <Typography variant="body1" gutterBottom>
              Trạng thái: 
              <span className={`status-${mlflowStatus}`} style={{ marginLeft: '8px' }}>
                {mlflowStatus === 'running' ? 'Đang chạy' : mlflowStatus === 'starting' ? 'Đang khởi động' : 'Dừng'}
              </span>
            </Typography>
            
            {mlflowStatus === 'running' && (
              <Box sx={{ mt: 2, mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  MLflow UI đang chạy tại:
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography 
                    variant="body2" 
                    component="a" 
                    href={mlflowUrl} 
                    target="_blank"
                    sx={{ color: 'primary.main', textDecoration: 'none', mr: 1 }}
                  >
                    {mlflowUrl}
                  </Typography>
                  <IconButton size="small" color="primary" onClick={openMlflowUi}>
                    <OpenInNewIcon fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
            )}
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Cấu hình Server
            </Typography>
            
            <TextField
              label="Port"
              name="port"
              type="number"
              value={config.port}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              disabled={mlflowStatus === 'running'}
              size="small"
            />
            
            <TextField
              label="Host"
              name="host"
              value={config.host}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              disabled={mlflowStatus === 'running'}
              size="small"
            />
            
            <TextField
              label="Artifact URI"
              name="artifact_uri"
              value={config.artifact_uri}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              disabled={mlflowStatus === 'running'}
              size="small"
            />
            
            <TextField
              label="Backend Store URI (optional)"
              name="backend_store_uri"
              value={config.backend_store_uri}
              onChange={handleConfigChange}
              fullWidth
              margin="normal"
              disabled={mlflowStatus === 'running'}
              size="small"
            />
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
              {mlflowStatus !== 'running' ? (
                <Button 
                  variant="contained" 
                  color="primary" 
                  startIcon={<PlayArrowIcon />}
                  onClick={startServer}
                  disabled={loading}
                  sx={{ minWidth: '180px' }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Start MLflow Server'}
                </Button>
              ) : (
                <Button 
                  variant="contained" 
                  color="error" 
                  startIcon={<StopIcon />}
                  onClick={stopServer}
                  disabled={loading}
                  sx={{ minWidth: '180px' }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Stop MLflow Server'}
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
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="mlflow data tabs">
              <Tab label="Experiments" />
              <Tab label="Runs" />
              <Tab label="Models" />
              <Tab label="Logs" />
            </Tabs>
          </Box>
          
          {/* Experiments Tab */}
          <TabPanel value={tabValue} index={0}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List sx={{ width: '100%' }}>
                {experiments.map((experiment) => (
                  <React.Fragment key={experiment.id}>
                    <ListItem>
                      <ListItemText
                        primary={experiment.name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              ID: {experiment.id}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Location: {experiment.artifact_location}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Runs: {experiment.runs}
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
                {runs.map((run) => (
                  <React.Fragment key={run.run_id}>
                    <ListItem>
                      <ListItemText
                        primary={`Run ID: ${run.run_id}`}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              Model: {run.model}
                            </Typography>
                            <br />
                            <Typography 
                              component="span" 
                              variant="body2" 
                              className={`status-${run.status === 'COMPLETED' ? 'running' : run.status === 'RUNNING' ? 'running' : 'stopped'}`}
                            >
                              Status: {run.status}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Started: {new Date(run.start_time).toLocaleString()}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Metrics: {Object.entries(run.metrics).map(([key, value]) => `${key}: ${value}`).join(', ')}
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
          
          {/* Models Tab */}
          <TabPanel value={tabValue} index={2}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List sx={{ width: '100%' }}>
                {models.map((model) => (
                  <React.Fragment key={model.name}>
                    <ListItem>
                      <ListItemText
                        primary={model.name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              Version: {model.version}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Stage: {model.stage}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2">
                              Last Updated: {new Date(model.last_updated).toLocaleString()}
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
          
          {/* Logs Tab */}
          <TabPanel value={tabValue} index={3}>
            <Paper className="logs-container">
              {logs.map((log, index) => (
                <Typography key={index} variant="body2" component="div" sx={{ fontFamily: 'monospace' }}>
                  {log}
                </Typography>
              ))}
              {logs.length === 0 && (
                <Typography variant="body2" color="textSecondary">
                  No logs available. Start the MLflow server to see logs.
                </Typography>
              )}
            </Paper>
          </TabPanel>
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
      id={`mlflow-tabpanel-${index}`}
      aria-labelledby={`mlflow-tab-${index}`}
      {...other}
      style={{ padding: '16px' }}
    >
      {value === index && children}
    </div>
  );
}

export default MLflowPage; 