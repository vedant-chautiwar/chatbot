import { apiRequest } from './client';

/**
 * Register a new account via FastAPI backend.
 * @param {string} email
 * @param {string} password
 * @param {string} [name]
 * @returns {Promise<{ access_token: string, token_type: string, user: object }>}
 */
export async function registerApi(email, password, name) {
  return await apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });
}

/**
 * Authenticate existing user via FastAPI backend.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{ access_token: string, token_type: string, user: object }>}
 */
export async function loginApi(email, password) {
  return await apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

/**
 * Retrieve verified profile for the currently authenticated user.
 * @returns {Promise<{ user_id: string, email: string, name?: string, role: string }>}
 */
export async function fetchCurrentUserApi() {
  return await apiRequest('/auth/me', {
    method: 'GET',
  });
}

/**
 * Terminate user session.
 */
export async function logoutApi() {
  try {
    return await apiRequest('/auth/logout', {
      method: 'POST',
    });
  } catch {
    return { message: 'Logged out locally' };
  }
}
