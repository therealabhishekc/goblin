/**
 * Date Formatter Utility
 * Converts UTC timestamps to CST/CDT (America/Chicago timezone)
 */

/**
 * Format a date string to CST timezone
 * @param {string|Date} dateString - ISO date string or Date object
 * @param {object} options - Optional formatting options
 * @returns {string} Formatted date string in CST or 'N/A' if invalid
 */
export const formatToCST = (dateString, options = {}) => {
  if (!dateString) return 'N/A';
  
  try {
    const defaultOptions = {
      timeZone: 'America/Chicago',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      timeZoneName: 'short',
      ...options
    };
    
    return new Date(dateString).toLocaleString('en-US', defaultOptions);
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

/**
 * Format a date without time (date only)
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Formatted date string in CST (MM/DD/YYYY)
 */
export const formatDateOnlyCST = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    return new Date(dateString).toLocaleString('en-US', {
      timeZone: 'America/Chicago',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

/**
 * Format a date with time but without timezone abbreviation
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Formatted date string in CST (MM/DD/YYYY, HH:MM:SS AM/PM)
 */
export const formatDateTimeCST = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    return new Date(dateString).toLocaleString('en-US', {
      timeZone: 'America/Chicago',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

/**
 * Format a date in a compact format
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Formatted date string in CST (M/D/YYYY h:MM AM/PM)
 */
export const formatDateCompactCST = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    return new Date(dateString).toLocaleString('en-US', {
      timeZone: 'America/Chicago',
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

/**
 * Get relative time (e.g., "2 hours ago")
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Relative time string
 */
export const getRelativeTime = (dateString) => {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval > 1) return `${interval} years ago`;
    if (interval === 1) return '1 year ago';
    
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) return `${interval} months ago`;
    if (interval === 1) return '1 month ago';
    
    interval = Math.floor(seconds / 86400);
    if (interval > 1) return `${interval} days ago`;
    if (interval === 1) return '1 day ago';
    
    interval = Math.floor(seconds / 3600);
    if (interval > 1) return `${interval} hours ago`;
    if (interval === 1) return '1 hour ago';
    
    interval = Math.floor(seconds / 60);
    if (interval > 1) return `${interval} minutes ago`;
    if (interval === 1) return '1 minute ago';
    
    if (seconds < 10) return 'just now';
    return `${Math.floor(seconds)} seconds ago`;
  } catch (error) {
    console.error('Error calculating relative time:', error);
    return 'Unknown';
  }
};

export default {
  formatToCST,
  formatDateOnlyCST,
  formatDateTimeCST,
  formatDateCompactCST,
  getRelativeTime
};
