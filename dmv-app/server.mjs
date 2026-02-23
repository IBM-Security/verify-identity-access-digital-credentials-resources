/**
 * Production server for DMV app
 * Serves static files and uses the same proxy configuration as development
 * ESM version for compatibility with openid-client v6+
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

console.log('Starting DMV app server with proxy configuration (ESM version)');

// Generate config.js with environment variables 
const configContent = `// Runtime environment configuration for DMV App
window.ENV = {
  // DMV app environment variables
  REACT_APP_ACCOUNT_URL: '${process.env.REACT_APP_ACCOUNT_URL || ''}',
  REACT_APP_W3_ROOT: '${process.env.REACT_APP_W3_ROOT || ''}',
  REACT_APP_DMV_REDIRECT_URL: '${process.env.REACT_APP_DMV_REDIRECT_URL || ''}',
  REACT_APP_CREDENTIAL_SCHEMA_ID: '${process.env.REACT_APP_CREDENTIAL_SCHEMA_ID || ''}',
  REACT_APP_CREDENTIAL_DEFINITION_ID: '${process.env.REACT_APP_CREDENTIAL_DEFINITION_ID || ''}'
};`;

// Write config.js to the build directory
const configPath = path.join(__dirname, 'build', 'config.js');
fs.writeFileSync(configPath, configContent);

console.log('Generated config.js with environment variables');
console.log(`REACT_APP_ACCOUNT_URL: ${process.env.REACT_APP_ACCOUNT_URL || ''}`);
console.log(`REACT_APP_W3_ROOT: ${process.env.REACT_APP_W3_ROOT || ''}`);
console.log(`REACT_APP_DMV_REDIRECT_URL: ${process.env.REACT_APP_DMV_REDIRECT_URL || ''}`);
console.log(`REACT_APP_CREDENTIAL_SCHEMA_ID: ${process.env.REACT_APP_CREDENTIAL_SCHEMA_ID || ''}`);
console.log(`REACT_APP_CREDENTIAL_DEFINITION_ID: ${process.env.REACT_APP_CREDENTIAL_DEFINITION_ID || ''}`);

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
  console.log(`DMV app server running on port ${PORT} (ESM version)`);
});

// Made with Bob
