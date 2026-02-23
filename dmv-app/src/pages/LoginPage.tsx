import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Button,
  Alert,
  Box,
  Stack,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Login as LoginIcon,
} from '@mui/icons-material';
import loginBgImage from '../images/login-bg-1.jpg';
import { useAuth } from '../components/AuthProvider';
import { Header } from '../components/Header';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();

  // If already logged in, redirect to profile settings
  useEffect(() => {
    // Check if we have a valid authentication state
    if (isAuthenticated) {
      navigate('/profile');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent default form submission
    setIsLoading(true);
    setError('');
    
    try {
      // Use the login function from AuthContext
      await login();
    } catch (err) {
      setError('Failed to initiate login. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="login-wrapper" style={{
      backgroundImage: `url(${loginBgImage})`
    }}>
      <Header isLoggedIn={false}/>
      <Container maxWidth="xl">
        <Grid className='login-grid' container spacing={4} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Paper
              elevation={4}
              sx={{
                p: 4
              }}
            >
              <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: "bold", mb: 4 }} >
                Sign in to your account
              </Typography>

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}
              
              <Box component="form" noValidate>
                <Stack spacing={3}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    size="large"
                    startIcon={<LoginIcon />}
                    onClick={handleLogin}
                    disabled={isLoading}
                    sx={{
                      py: 1.5,
                      mt: 2,
                      borderRadius: 2
                    }}
                  >
                    {isLoading ? 'Signing in...' : 'Sign in with IBM Verify'}
                  </Button>
                </Stack>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
};

export default LoginPage;

// Made with Bob
