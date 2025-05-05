import React from 'react';
import { Box, Typography, Card, CardContent, Button } from '@mui/material';
import FolderIcon from '@mui/icons-material/Folder';

const FileManagerPage = () => {
  return (
    <Box sx={{ padding: 3 }}>
      <Typography variant="h4" gutterBottom>
        File Manager
      </Typography>
      
      <Card sx={{ maxWidth: '100%', mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FolderIcon fontSize="large" color="primary" sx={{ mr: 2 }} />
            <Typography variant="h6">
              File Management Interface
            </Typography>
          </Box>
          
          <Typography variant="body1" paragraph>
            This is the file manager interface for the MLOps dashboard. This component will be implemented to allow users to browse, upload, and manage files related to ML projects.
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button variant="contained" color="primary" disabled>
              Coming Soon
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FileManagerPage; 