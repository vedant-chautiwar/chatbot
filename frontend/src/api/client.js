/**
 * Centralized API Client for Agentic AI Chatbot Backend
 */

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
// Normalize base URL: strip trailing slash
export const API_BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

let currentAuthToken = null;

/**
 * Configure the current bearer access token for outgoing API requests
 */
export function setAuthToken(token) {
  currentAuthToken = token || null;
}

export function getAuthToken() {
  return currentAuthToken;
}

/**
 * Custom API Error class with normalized backend detail
 */
export class ApiError extends Error {
  constructor(message, status = 0, errors = null, raw = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errors = errors;
    this.raw = raw;
  }
}

/**
 * Make an HTTP request to the backend with authentication and standardized error handling
 */
export async function apiRequest(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;

  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  // Attach Authorization header if token is configured
  if (currentAuthToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`;
  }

  // Set Content-Type for JSON payloads if not explicitly set
  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 204) {
      return null;
    }

    const contentType = response.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      let validationErrors = null;
      let rawData = null;

      if (isJson) {
        try {
          rawData = await response.json();
          if (typeof rawData.detail === 'string') {
            errorMessage = rawData.detail;
          } else if (Array.isArray(rawData.errors)) {
            // FastAPI custom validation handler format
            errorMessage = rawData.detail || 'Validation error';
            validationErrors = rawData.errors;
          } else if (Array.isArray(rawData.detail)) {
            // Default FastAPI validation error format
            errorMessage = rawData.detail.map(e => `${e.loc?.join('.') || 'field'}: ${e.msg}`).join(', ');
            validationErrors = rawData.detail;
          }
        } catch {
          // Fallback to generic message
        }
      } else {
        try {
          const text = await response.text();
          if (text) errorMessage = text;
        } catch {
          // Keep default status message
        }
      }

      throw new ApiError(errorMessage, response.status, validationErrors, rawData);
    }

    if (isJson) {
      return await response.json();
    }
    return await response.text();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network error / Connection refused
    console.error('API connection failure:', error);
    throw new ApiError(
      'Unable to connect to backend server. Please verify the FastAPI service is running at ' + API_BASE_URL,
      0,
      null,
      error
    );
  }
}
