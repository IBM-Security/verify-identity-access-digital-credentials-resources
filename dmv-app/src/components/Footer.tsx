import React from 'react';
import { Container, Box, Typography, Link } from '@mui/material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.background.paper,
        borderTop: (theme) => `1px solid ${theme.palette.divider}`
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'center', md: 'flex-start' } }}>
          <Box sx={{ mb: { xs: 2, md: 0 } }}>
            <Typography variant="body2" color="text.secondary">
              © {new Date().getFullYear()} Department of Motor Vehicles. All rights reserved.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Link href="#" color="primary" underline="hover">Privacy Policy</Link>
            <Link href="#" color="primary" underline="hover">Terms of Service</Link>
            <Link href="#" color="primary" underline="hover">Contact Us</Link>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
