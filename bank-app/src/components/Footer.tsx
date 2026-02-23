import React from 'react';
import { Container, Box, Typography, Link, Divider } from '@mui/material';
import Grid from '@mui/material/Grid';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 6,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.background.paper,
        borderTop: (theme) => `1px solid ${theme.palette.divider}`
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid size={{ xs: 12, md: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Box 
                component="div" 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  mr: 1,
                  backgroundColor: '#5E5CFF',
                  width: 32,
                  height: 32,
                  borderRadius: 1,
                  justifyContent: 'center'
                }}
              >
                <Typography variant="subtitle1" sx={{ color: 'white', fontWeight: 'bold' }}>
                  S.
                </Typography>
              </Box>
              <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                Smart money
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Manage your finances effortlessly with our advanced banking solutions. Safe, fast, and designed for your everyday needs.
            </Typography>
          </Grid>
          
          <Grid size={{ xs: 6, md: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
              Pages
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Home</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>About</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Pricing</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Features</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Affiliates</Link>
            </Box>
          </Grid>
          
          <Grid size={{ xs: 6, md: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
              Company
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Our Team</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Mission and Values</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Social Media</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>FAQ</Link>
            </Box>
          </Grid>
          
          <Grid size={{ xs: 6, md: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
              Developers
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>API Documentation</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Developer Tools</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Status</Link>
            </Box>
          </Grid>
          
          <Grid size={{ xs: 6, md: 3 }}>
            <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
              Resources
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Contact Us</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Blog</Link>
              <Link href="#" color="text.secondary" underline="hover" onClick={(e) => e.preventDefault()}>Help Center</Link>
            </Box>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 4 }} />
        
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'center', md: 'center' } }}>
          <Typography variant="body2" color="text.secondary">
            Copyright © 2024 Smart Money. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;

// Made with Bob
