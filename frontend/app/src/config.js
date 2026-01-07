// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://2hdfnnus3x.us-east-1.awsapprunner.com';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'wss://2hdfnnus3x.us-east-1.awsapprunner.com';

export const config = {
  apiUrl: API_BASE_URL,
  wsUrl: WS_BASE_URL,
  endpoints: {
    // Health
    health: '/health',
    
    // Authentication & Users
    users: '/api/users',
    login: '/api/users/login',
    register: '/api/users/register',
    
    // Admin
    admin: {
      users: '/api/admin/users',
      analytics: '/api/admin/analytics',
      settings: '/api/admin/settings',
    },
    
    // Messaging
    messages: '/api/messages',
    sendMessage: '/api/messages/send',
    sendTemplate: '/api/messages/send-template',
    
    // Marketing Campaigns
    campaigns: '/api/marketing/campaigns',
    campaignById: (id) => `/api/marketing/campaigns/${id}`,
    campaignStart: (id) => `/api/marketing/campaigns/${id}/start`,
    campaignPause: (id) => `/api/marketing/campaigns/${id}/pause`,
    
    // Analytics
    analytics: '/api/analytics',
    dashboardStats: '/api/analytics/dashboard',
    messageStats: '/api/analytics/messages',
    campaignStats: '/api/analytics/campaigns',
    
    // Archive
    archive: {
      messages: '/api/archive/messages',
      media: '/api/archive/media',
    },
    
    // Monitoring
    monitoring: {
      health: '/api/monitoring/health',
      metrics: '/api/monitoring/metrics',
    },
    
    // WebSocket
    ws: '/ws',
  },
};

export default config;
