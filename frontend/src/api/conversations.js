/**
 * Conversation API endpoints matching FastAPI routes
 */

import { apiRequest } from './client';

/**
 * List user's conversations with pagination
 * @param {Object} params
 * @param {number} [params.limit=20]
 * @param {number} [params.offset=0]
 */
export async function fetchConversations({ limit = 30, offset = 0 } = {}) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  return await apiRequest(`/conversations?${query.toString()}`);
}

/**
 * Create a new conversation explicitly
 * @param {Object} [params]
 * @param {string} [params.title]
 */
export async function createConversation({ title = null } = {}) {
  return await apiRequest('/conversations', {
    method: 'POST',
    body: JSON.stringify(title ? { title } : {}),
  });
}

/**
 * Fetch a single conversation and its message history
 * @param {string} conversationId
 * @param {Object} [params]
 * @param {number} [params.limit=50]
 * @param {number} [params.offset=0]
 */
export async function fetchConversationDetails(conversationId, { limit = 50, offset = 0 } = {}) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  return await apiRequest(`/conversations/${conversationId}?${query.toString()}`);
}

/**
 * Rename an existing conversation
 * @param {string} conversationId
 * @param {string} newTitle
 */
export async function renameConversation(conversationId, newTitle) {
  return await apiRequest(`/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title: newTitle }),
  });
}

/**
 * Delete a conversation and all its associated messages
 * @param {string} conversationId
 */
export async function deleteConversation(conversationId) {
  return await apiRequest(`/conversations/${conversationId}`, {
    method: 'DELETE',
  });
}
