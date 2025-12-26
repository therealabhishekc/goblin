// API Configuration
// Change this based on your environment

const config = {
  // For local development
  LOCAL_API_URL: 'http://localhost:8000',
  
  // For production (AWS App Runner)
  // UPDATE THIS with your App Runner URL
  PRODUCTION_API_URL: 'https://unihkhw6ee.us-east-1.awsapprunner.com',
  
  // Current environment
  // Uses REACT_APP_API_URL env var if set, otherwise defaults to PRODUCTION_API_URL
  API_URL: process.env.REACT_APP_API_URL || 'https://unihkhw6ee.us-east-1.awsapprunner.com'
};

export default config;
