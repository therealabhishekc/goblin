import axios from 'axios';
import { config } from '../config';

// Create axios instance with default config
const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API Service methods
export const apiService = {
  // Health
  checkHealth: () => api.get(config.endpoints.health),
  
  // Users
  getUsers: () => api.get(config.endpoints.users),
  getUserById: (id) => api.get(`${config.endpoints.users}/${id}`),
  createUser: (data) => api.post(config.endpoints.users, data),
  updateUser: (id, data) => api.put(`${config.endpoints.users}/${id}`, data),
  deleteUser: (id) => api.delete(`${config.endpoints.users}/${id}`),
  
  // Authentication
  login: (credentials) => api.post(config.endpoints.login, credentials),
  register: (userData) => api.post(config.endpoints.register, userData),
  
  // Messages
  getMessages: (params) => api.get(config.endpoints.messages, { params }),
  sendMessage: (data) => api.post(config.endpoints.sendMessage, data),
  sendTemplate: (data) => api.post(config.endpoints.sendTemplate, data),
  
  // Marketing Campaigns
  getCampaigns: () => api.get(config.endpoints.campaigns),
  getCampaignById: (id) => api.get(config.endpoints.campaignById(id)),
  createCampaign: (data) => api.post(config.endpoints.campaigns, data),
  updateCampaign: (id, data) => api.put(config.endpoints.campaignById(id), data),
  deleteCampaign: (id) => api.delete(config.endpoints.campaignById(id)),
  startCampaign: (id) => api.post(config.endpoints.campaignStart(id)),
  pauseCampaign: (id) => api.post(config.endpoints.campaignPause(id)),
  
  // Analytics
  getDashboardStats: () => api.get(config.endpoints.dashboardStats),
  getMessageStats: (params) => api.get(config.endpoints.messageStats, { params }),
  getCampaignStats: (params) => api.get(config.endpoints.campaignStats, { params }),
  
  // Archive
  getArchivedMessages: (params) => api.get(config.endpoints.archive.messages, { params }),
  getArchivedMedia: (params) => api.get(config.endpoints.archive.media, { params }),
  
  // Monitoring
  getHealthMetrics: () => api.get(config.endpoints.monitoring.health),
  getSystemMetrics: () => api.get(config.endpoints.monitoring.metrics),
  
  // Templates
  getTemplates: (params) => api.get('/templates', { params }),
  getTemplateById: (id) => api.get(`/templates/${id}`),
  getTemplateByName: (name) => api.get(`/templates/name/${name}`),
  createTemplate: (data) => api.post('/templates', data),
  updateTemplate: (id, data) => api.put(`/templates/${id}`, data),
  deleteTemplate: (id) => api.delete(`/templates/${id}`),
  toggleTemplateStatus: (id) => api.post(`/templates/${id}/toggle`),
};

export default api;
