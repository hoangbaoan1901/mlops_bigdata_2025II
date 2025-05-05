import React, { useState, useEffect } from 'react';
import { Box, Paper } from '@mui/material';
import { mlflowApi } from '../services/api';

const ModelRegistryPage = () => {
  const [mlflowUrl] = useState('http://localhost:5000');
  const [iframeKey, setIframeKey] = useState(Date.now());

  // Tự động làm mới iframe mỗi khi component được mount
  useEffect(() => {
    setIframeKey(Date.now());
  }, []);

  return (
    <Box sx={{ 
      width: '100%',
      height: 'calc(100vh - 40px)', // Adjust to leave space for navbar
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <iframe
        key={iframeKey}
        src={mlflowUrl + "#/models"}
        style={{
          width: '100%',
          height: '100%',
          border: 'none'
        }}
        title="MLflow Model Registry"
      />
    </Box>
  );
};

export default ModelRegistryPage;