import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

// Component imports
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import MLflowPage from './pages/MLflowPage';
import KubeflowPage from './pages/KubeflowPage';
import ModelRegistryPage from './pages/ModelRegistryPage';
import KServePage from './pages/KServePage';
import MockModeProvider from './context/MockModeContext';

// Create custom theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#4527A0',
    },
    secondary: {
      main: '#5E35B1',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      color: '#4527A0',
    },
    h2: {
      fontSize: '1.8rem',
      fontWeight: 600,
      color: '#5E35B1',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 5,
          textTransform: 'none',
        },
        containedPrimary: {
          backgroundColor: '#4527A0',
          '&:hover': {
            backgroundColor: '#311B92',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <MockModeProvider>
        <CssBaseline />
        <div style={{ display: 'flex' }}>
          <Sidebar />
          <div style={{ flexGrow: 1, padding: '20px' }}>
            {/* <Header /> */}
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/mlflow" element={<MLflowPage />} />
              <Route path="/kubeflow" element={<KubeflowPage />} />
              <Route path="/model-registry" element={<ModelRegistryPage />} />
              <Route path="/kserve" element={<KServePage />} />
            </Routes>
          </div>
        </div>
      </MockModeProvider>
    </ThemeProvider>
  );
}

export default App; 