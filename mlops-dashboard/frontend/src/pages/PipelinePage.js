import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';

const PipelinePage = () => {
  const [kubeflowUrl] = useState('http://localhost:8080');
  const [iframeKey, setIframeKey] = useState(Date.now());

  // Automatically refresh iframe when component mounts
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
        src={kubeflowUrl + "/#/pipelines"}
        style={{
          width: '100%',
          height: '100%',
          border: 'none'
        }}
        title="Kubeflow Pipelines"
      />
    </Box>
  );
};

export default PipelinePage; 