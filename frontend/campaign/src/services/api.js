/**
 * API Service for Campaign Manager
 * Handles all HTTP requests to the backend API
 */
import axios from 'axios';
import config from '../config';

// Configure axios defaults - no /api prefix needed
const API_BASE_URL = config.API_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🌐 ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ Response:`, response.data);
    return response;
  },
  (error) => {
    console.error(`❌ API Error:`, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Campaign API endpoints
export const campaignAPI = {
  // Create a new campaign
  createCampaign: async (campaignData) => {
    const response = await api.post('/marketing/campaigns', campaignData);
    return response.data;
  },

  // Get all campaigns
  listCampaigns: async (status = null, limit = 50) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await api.get('/marketing/campaigns', { params });
    return response.data;
  },

  // Get campaign statistics
  getCampaignStats: async (campaignId) => {
    const response = await api.get(`/marketing/campaigns/${campaignId}/stats`);
    return response.data;
  },

  // Add recipients to campaign
  addRecipients: async (campaignId, data) => {
    const response = await api.post(`/marketing/campaigns/${campaignId}/recipients`, data);
    return response.data;
  },

  // Add recipients using target audience
  addRecipientsFromAudience: async (campaignId) => {
    const response = await api.post(
      `/marketing/campaigns/${campaignId}/recipients?use_target_audience=true`
    );
    return response.data;
  },

  // Activate campaign
  activateCampaign: async (campaignId, startDate = null) => {
    const params = startDate ? { start_date: startDate } : {};
    const response = await api.post(`/marketing/campaigns/${campaignId}/activate`, null, { params });
    return response.data;
  },

  // Pause campaign
  pauseCampaign: async (campaignId) => {
    const response = await api.post(`/marketing/campaigns/${campaignId}/pause`);
    return response.data;
  },

  // Resume campaign
  resumeCampaign: async (campaignId) => {
    const response = await api.post(`/marketing/campaigns/${campaignId}/resume`);
    return response.data;
  },

  // Cancel campaign
  cancelCampaign: async (campaignId) => {
    const response = await api.post(`/marketing/campaigns/${campaignId}/cancel`);
    return response.data;
  },

  // Process daily campaigns (admin only)
  processDailyCampaigns: async () => {
    const response = await api.post('/marketing/process-daily');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/marketing/health');
    return response.data;
  },
};

// User API endpoints (for recipient selection)
export const userAPI = {
  // Get all users
  listUsers: async () => {
    const response = await api.get('/users');
    return response.data;
  },

  // Get subscribed users only
  getSubscribedUsers: async () => {
    const response = await api.get('/users?subscription=subscribed');
    return response.data;
  },
};

export default api;
