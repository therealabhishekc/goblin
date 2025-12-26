/**
 * Utility functions for formatting data
 */
import { format, parseISO } from 'date-fns';

/**
 * Format date string to readable format
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return format(parseISO(dateString), 'MMM dd, yyyy');
  } catch {
    return dateString;
  }
};

/**
 * Format date and time
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
  } catch {
    return dateString;
  }
};

/**
 * Format number with commas
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  return num.toLocaleString();
};

/**
 * Format percentage
 */
export const formatPercentage = (value) => {
  if (value === null || value === undefined) return '0%';
  return `${value.toFixed(1)}%`;
};

/**
 * Get status badge color
 */
export const getStatusColor = (status) => {
  const colors = {
    draft: '#6c757d',      // gray
    active: '#28a745',     // green
    paused: '#ffc107',     // yellow
    completed: '#17a2b8',  // blue
    cancelled: '#dc3545',  // red
  };
  return colors[status] || '#6c757d';
};

/**
 * Get status display text
 */
export const getStatusText = (status) => {
  const texts = {
    draft: 'Draft',
    active: 'Active',
    paused: 'Paused',
    completed: 'Completed',
    cancelled: 'Cancelled',
  };
  return texts[status] || status;
};

/**
 * Calculate progress percentage
 */
export const calculateProgress = (sent, total) => {
  if (!total || total === 0) return 0;
  return Math.round((sent / total) * 100);
};

/**
 * Format phone number
 */
export const formatPhoneNumber = (phone) => {
  if (!phone) return '';
  // Remove any non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  // Format as +1 (XXX) XXX-XXXX for US numbers
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  // Return with + prefix for international
  return `+${cleaned}`;
};

/**
 * Parse phone number input to clean format
 */
export const parsePhoneNumber = (input) => {
  // Remove all non-digit characters
  return input.replace(/\D/g, '');
};

/**
 * Validate phone number
 */
export const isValidPhoneNumber = (phone) => {
  const cleaned = phone.replace(/\D/g, '');
  // Must be 10-15 digits
  return cleaned.length >= 10 && cleaned.length <= 15;
};

/**
 * Format duration in days
 */
export const formatDuration = (days) => {
  if (!days) return '0 days';
  if (days === 1) return '1 day';
  return `${days} days`;
};
