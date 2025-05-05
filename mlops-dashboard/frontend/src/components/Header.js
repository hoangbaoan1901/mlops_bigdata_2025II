import React from 'react';
import { AppBar, Toolbar, Typography, Box, Switch, FormControlLabel } from '@mui/material';
import { useMockMode } from '../context/MockModeContext';

const Header = () => {
  const { mockMode, toggleMockMode } = useMockMode();

  return (
    <AppBar position="static" color="primary" elevation={0} sx={{ mb: 3, borderRadius: 2 }}>
      <Toolbar>
        <Typography variant="h1" component="div" sx={{ flexGrow: 1, fontSize: '1.5rem' }}>
          MLOps Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch 
                checked={mockMode} 
                onChange={toggleMockMode} 
                color="default"
                sx={{ 
                  '& .MuiSwitch-switchBase.Mui-checked': { 
                    color: 'white',
                  },
                  '& .MuiSwitch-track': {
                    backgroundColor: mockMode ? 'rgba(255, 255, 255, 0.5)' : 'rgba(255, 255, 255, 0.3)',
                  }
                }} 
              />
            }
            label={
              <Typography color="white">
                Chế độ xem trước UI
              </Typography>
            }
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 