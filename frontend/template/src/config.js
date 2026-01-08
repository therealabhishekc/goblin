// API Configuration
// Change this based on your environment

const config = {
  // For local development
  LOCAL_API_URL: 'http://localhost:8000',
  
  // For production (AWS App Runner)
  PRODUCTION_API_URL: 'https://byqpifhtjq.us-east-1.awsapprunner.com',
  
  // Current environment - configured directly in this file
  // Change this to LOCAL_API_URL for local development
  API_URL: 'https://byqpifhtjq.us-east-1.awsapprunner.com'
};

export default config;
