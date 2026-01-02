// API Configuration
// Change this based on your environment

const config = {
  // For local development
  LOCAL_API_URL: 'http://localhost:8000',
  
  // For production (AWS App Runner)
  PRODUCTION_API_URL: 'https://g5yeutappx.us-east-1.awsapprunner.com',
  
  // Current environment
  API_URL: process.env.REACT_APP_API_URL || 'https://g5yeutappx.us-east-1.awsapprunner.com'
};

export default config;
