import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: config.API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Log API URL on startup
console.log('🔗 API Base URL:', config.API_URL);

// Get all templates
export const getTemplates = async () => {
  try {
    const response = await api.get('/templates/');
    return response.data;
  } catch (error) {
    console.error('Error fetching templates:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch templates');
  }
};

// Get single template by ID
export const getTemplate = async (id) => {
  try {
    const response = await api.get(`/templates/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching template:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch template');
  }
};

// Create new template
export const createTemplate = async (templateData) => {
  try {
    console.log('🔍 Creating template with data:', templateData);
    const response = await api.post('/templates/', templateData);
    console.log('✅ Template created successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error creating template:', error);
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    });
    throw new Error(error.response?.data?.detail || error.message || 'Failed to create template');
  }
};

// Update existing template
export const updateTemplate = async (id, templateData) => {
  try {
    const response = await api.put(`/templates/${id}`, templateData);
    return response.data;
  } catch (error) {
    console.error('Error updating template:', error);
    throw new Error(error.response?.data?.detail || 'Failed to update template');
  }
};

// Delete template
export const deleteTemplate = async (id) => {
  try {
    const response = await api.delete(`/templates/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting template:', error);
    throw new Error(error.response?.data?.detail || 'Failed to delete template');
  }
};

export default api;
