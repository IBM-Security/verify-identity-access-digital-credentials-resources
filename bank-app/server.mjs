/**
 * Production server for Bank app
 * Serves static files and uses the same proxy configuration as development
 * ESM version for consistency with dmv-app
 */
import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import setupRoutes from './src/setupRoutes.mjs';

// ESM doesn't have __dirname, so we need to create it
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

console.log('Starting Bank app server with proxy configuration (ESM version)');

// Generate config.js with environment variables
const configContent = `// Runtime environment configuration for Bank App
window.ENV = {
  // Bank app environment variables
  REACT_APP_ACCOUNT_URL: '${process.env.REACT_APP_ACCOUNT_URL || ''}',
  REACT_APP_EXCHANGE_TEMPLATE_ID: '${process.env.REACT_APP_EXCHANGE_TEMPLATE_ID || ''}'
};`;

// Write config.js to the build directory
const configPath = path.join(__dirname, 'build', 'config.js');
fs.writeFileSync(configPath, configContent);

console.log('Generated config.js with environment variables');
console.log(`REACT_APP_ACCOUNT_URL: ${process.env.REACT_APP_ACCOUNT_URL || ''}`);
console.log(`REACT_APP_EXCHANGE_TEMPLATE_ID: ${process.env.REACT_APP_EXCHANGE_TEMPLATE_ID || ''}`);

// Apply the proxy configuration to our production server
setupRoutes(app);

// Set the correct MIME type for config.js
app.get('/config.js', (req, res) => {
  res.setHeader('Content-Type', 'application/javascript');
  res.sendFile(configPath);
});

// Serve static files from the build directory
app.use(express.static(path.join(__dirname, 'build')));

// For all other requests, serve the React app
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`Bank app server running on port ${PORT} (ESM version)`);
});

// Made with Bob