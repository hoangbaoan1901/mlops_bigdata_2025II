import React from 'react';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Divider,
  Box,
  Typography
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import BarChartIcon from '@mui/icons-material/BarChart';
import StorageIcon from '@mui/icons-material/Storage';
import CategoryIcon from '@mui/icons-material/Category';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';

const drawerWidth = 240;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'MLflow Server', icon: <BarChartIcon />, path: '/mlflow' },
    { text: 'Kubeflow Pipelines', icon: <StorageIcon />, path: '/kubeflow' },
    { text: 'Model Registry', icon: <CategoryIcon />, path: '/model-registry' },
    { text: 'KServe', icon: <CloudQueueIcon />, path: '/kserve' },
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#f8f9fa',
          borderRight: '1px solid #e0e0e0',
        },
      }}
    >
      <Box sx={{ p: 2, textAlign: 'center', mb: 2 }}>
        <Typography variant="h6" color="primary" fontWeight="bold">
          MLOps Dashboard
        </Typography>
        <Typography variant="caption" color="textSecondary">
          v1.0.0
        </Typography>
      </Box>
      
      <Divider />
      
      <List>
        {menuItems.map((item) => (
          <ListItem 
            button 
            key={item.text} 
            onClick={() => navigate(item.path)}
            selected={location.pathname === item.path}
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'rgba(69, 39, 160, 0.1)',
                borderRight: '4px solid #4527A0',
                '&:hover': {
                  backgroundColor: 'rgba(69, 39, 160, 0.2)',
                },
              },
              '&:hover': {
                backgroundColor: 'rgba(69, 39, 160, 0.05)',
              },
            }}
          >
            <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText 
              primary={item.text} 
              primaryTypographyProps={{ 
                fontWeight: location.pathname === item.path ? 'bold' : 'normal',
                color: location.pathname === item.path ? 'primary' : 'inherit',
              }} 
            />
          </ListItem>
        ))}
      </List>
      
      <Divider />
      
      <Box sx={{ position: 'absolute', bottom: 0, width: '100%', p: 2 }}>
        <Typography variant="body2" color="textSecondary" align="center">
          © 2023 MLOps Dashboard
        </Typography>
      </Box>
    </Drawer>
  );
};

export default Sidebar; 