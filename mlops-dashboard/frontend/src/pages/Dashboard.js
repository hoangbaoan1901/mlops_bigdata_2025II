import React, { useState, useEffect } from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  CardHeader, 
  Divider,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
  Box,
  Chip
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import BarChartIcon from '@mui/icons-material/BarChart';
import CategoryIcon from '@mui/icons-material/Category';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import { useNavigate } from 'react-router-dom';
import { useMockMode } from '../context/MockModeContext';
import { mlflowApi, kubeflowApi, kserveApi } from '../services/api';

// Giao diện của các biểu đồ trong trang dashboard
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Pie, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Dashboard = () => {
  const navigate = useNavigate();
  const { mockMode } = useMockMode();
  
  const [mlflowStatus, setMlflowStatus] = useState('stopped');
  const [experiments, setExperiments] = useState([]);
  const [runs, setRuns] = useState([]);
  const [pipelines, setPipelines] = useState([]);
  const [models, setModels] = useState([]);
  const [deployments, setDeployments] = useState([]);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        if (mockMode) {
          // Lấy dữ liệu mẫu trong chế độ xem trước
          const experimentRes = await mlflowApi.getMockExperiments();
          const runsRes = await mlflowApi.getMockRuns();
          const pipelinesRes = await kubeflowApi.getMockPipelines();
          const modelsRes = await mlflowApi.getMockModels();
          
          // Simulate KServe deployments
          const mockDeployments = [
            {
              name: 'customer-churn-predictor',
              framework: 'sklearn',
              status: 'Running',
              replicas: 2
            },
            {
              name: 'fraud-detection',
              framework: 'xgboost',
              status: 'Running',
              replicas: 3
            },
            {
              name: 'image-classifier',
              framework: 'tensorflow',
              status: 'Failed',
              replicas: 0
            }
          ];
          
          setExperiments(experimentRes.data.experiments);
          setRuns(runsRes.data.runs);
          setPipelines(pipelinesRes.data.pipelines);
          setModels(modelsRes.data.models);
          setDeployments(mockDeployments);
        } else {
          // Lấy trạng thái MLflow thực tế
          const statusRes = await mlflowApi.getStatus();
          setMlflowStatus(statusRes.data.status);
          
          // Lấy dữ liệu mẫu khi không ở chế độ mock
          const experimentRes = await mlflowApi.getMockExperiments();
          const runsRes = await mlflowApi.getMockRuns();
          const pipelinesRes = await kubeflowApi.getMockPipelines();
          const modelsRes = await mlflowApi.getMockModels();
          
          // Simulate KServe deployments
          const mockDeployments = [
            {
              name: 'customer-churn-predictor',
              framework: 'sklearn',
              status: 'Running',
              replicas: 2
            },
            {
              name: 'fraud-detection',
              framework: 'xgboost',
              status: 'Running',
              replicas: 3
            },
            {
              name: 'image-classifier',
              framework: 'tensorflow',
              status: 'Failed',
              replicas: 0
            }
          ];
          
          setExperiments(experimentRes.data.experiments);
          setRuns(runsRes.data.runs);
          setPipelines(pipelinesRes.data.pipelines);
          setModels(modelsRes.data.models);
          setDeployments(mockDeployments);
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };
    
    fetchData();
  }, [mockMode]);
  
  // Data cho chart
  const experimentsData = {
    labels: experiments.map(exp => exp.name),
    datasets: [
      {
        label: 'Số lượng runs',
        data: experiments.map(exp => exp.runs),
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };
  
  const runStatusData = {
    labels: ['Completed', 'Running', 'Failed'],
    datasets: [
      {
        label: 'Run Status',
        data: [
          runs.filter(run => run.status === 'COMPLETED').length,
          runs.filter(run => run.status === 'RUNNING').length,
          runs.filter(run => run.status === 'FAILED').length,
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 99, 132, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };
  
  const modelStageData = {
    labels: ['Production', 'Staging', 'None'],
    datasets: [
      {
        label: 'Model Stages',
        data: [
          models.filter(model => model.stage === 'Production').length,
          models.filter(model => model.stage === 'Staging').length,
          models.filter(model => model.stage === 'None').length,
        ],
        backgroundColor: [
          'rgba(76, 175, 80, 0.6)',
          'rgba(33, 150, 243, 0.6)',
          'rgba(158, 158, 158, 0.6)',
        ],
        borderColor: [
          'rgba(76, 175, 80, 1)',
          'rgba(33, 150, 243, 1)',
          'rgba(158, 158, 158, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };
  
  const deploymentStatusData = {
    labels: ['Running', 'Creating', 'Failed'],
    datasets: [
      {
        label: 'Deployment Status',
        data: [
          deployments.filter(d => d.status === 'Running').length,
          deployments.filter(d => d.status === 'Creating').length,
          deployments.filter(d => d.status === 'Failed').length,
        ],
        backgroundColor: [
          'rgba(76, 175, 80, 0.6)',
          'rgba(33, 150, 243, 0.6)',
          'rgba(244, 67, 54, 0.6)',
        ],
        borderColor: [
          'rgba(76, 175, 80, 1)',
          'rgba(33, 150, 243, 1)',
          'rgba(244, 67, 54, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };
  
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'ML Experiments',
      },
    },
  };
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h2" gutterBottom>
          Tổng quan MLOps
        </Typography>
        <Typography variant="body1" paragraph>
          Quản lý và theo dõi các thí nghiệm ML, pipelines, mô hình và triển khai.
        </Typography>
      </Grid>
      
      {/* Status Cards */}
      <Grid item xs={12} md={6} lg={3}>
        <Card>
          <CardHeader 
            title="MLflow Server" 
            titleTypographyProps={{ variant: 'h6' }}
            avatar={<BarChartIcon color="primary" />}
          />
          <Divider />
          <CardContent>
            <Typography variant="body1" paragraph>
              Trạng thái: 
              <span className={`status-${mlflowStatus}`} style={{ marginLeft: '8px' }}>
                {mlflowStatus === 'running' ? 'Đang chạy' : 'Dừng'}
              </span>
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Typography variant="body2">
                {`${experiments.length} experiments`}
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                size="small"
                onClick={() => navigate('/mlflow')}
              >
                Xem Chi tiết
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card>
          <CardHeader 
            title="Kubeflow Pipelines" 
            titleTypographyProps={{ variant: 'h6' }}
            avatar={<StorageIcon color="primary" />}
          />
          <Divider />
          <CardContent>
            <Typography variant="body1" paragraph>
              {pipelines.length} pipelines sẵn sàng
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Typography variant="body2">
                ML workflows
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                size="small"
                onClick={() => navigate('/kubeflow')}
              >
                Xem Chi tiết
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card>
          <CardHeader 
            title="Model Registry" 
            titleTypographyProps={{ variant: 'h6' }}
            avatar={<CategoryIcon color="primary" />}
          />
          <Divider />
          <CardContent>
            <Typography variant="body1" paragraph>
              {models.length} models đã đăng ký
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Typography variant="body2">
                Quản lý phiên bản
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                size="small"
                onClick={() => navigate('/model-registry')}
              >
                Xem Chi tiết
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card>
          <CardHeader 
            title="KServe" 
            titleTypographyProps={{ variant: 'h6' }}
            avatar={<CloudQueueIcon color="primary" />}
          />
          <Divider />
          <CardContent>
            <Typography variant="body1" paragraph>
              {deployments.length} deployments
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Typography variant="body2">
                Triển khai mô hình
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                size="small"
                onClick={() => navigate('/kserve')}
              >
                Xem Chi tiết
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      {/* Charts */}
      <Grid item xs={12} md={6}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Thí nghiệm ML</Typography>
          <Bar options={chartOptions} data={experimentsData} height={250} />
        </Paper>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Trạng thái Runs</Typography>
          <Pie data={runStatusData} />
        </Paper>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Model Stages</Typography>
          <Doughnut data={modelStageData} height={250} />
        </Paper>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Triển khai Mô hình</Typography>
          <Pie data={deploymentStatusData} height={250} />
        </Paper>
      </Grid>
      
      {/* Recent Activity */}
      <Grid item xs={12}>
        <Card>
          <CardHeader 
            title="Hoạt động gần đây" 
            titleTypographyProps={{ variant: 'h6' }}
          />
          <Divider />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <CloudQueueIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Model 'customer-churn-predictor' đã được triển khai"
                  secondary="2023-05-01 10:30:00 - Replicas: 2"
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <CategoryIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Model 'customer_churn_predictor' version 3 đã được chuyển sang Production"
                  secondary="2023-05-01 10:25:00 - User: admin"
                />
              </ListItem>
              <Divider />
              {runs.slice(0, 1).map((run, index) => (
                <React.Fragment key={run.run_id}>
                  <ListItem>
                    <ListItemIcon>
                      <BarChartIcon color={run.status === 'COMPLETED' ? 'success' : run.status === 'RUNNING' ? 'info' : 'error'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={`Run ID: ${run.run_id}`}
                      secondary={`Model: ${run.model}, Status: ${run.status}`}
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default Dashboard; 