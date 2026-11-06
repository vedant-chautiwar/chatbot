/**
 * Document Analysis & Upload API Client
 */

import { API_BASE_URL, getAuthToken, apiRequest, ApiError } from './client';

/**
 * Upload a document (PDF, TXT, MD, or code) with progress tracking.
 *
 * @param {Object} params
 * @param {File} params.file
 * @param {string|null} [params.conversationId=null]
 * @param {function} [params.onProgress] Callback with upload percentage (0 - 100)
 * @returns {Promise<Object>} Document upload response metadata
 */
export function uploadDocument({ file, conversationId = null, onProgress = null }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const url = `${API_BASE_URL}/documents/upload`;
    const token = getAuthToken();

    xhr.open('POST', url);

    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    if (onProgress && xhr.upload) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      let data = null;
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        data = xhr.responseText;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
      } else {
        const errorMsg = (data && data.detail) || `Upload failed with status ${xhr.status}`;
        reject(new ApiError(errorMsg, xhr.status, null, data));
      }
    };

    xhr.onerror = () => {
      reject(new ApiError('Network error occurred during document upload.', 0));
    };

    const formData = new FormData();
    formData.append('file', file);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    xhr.send(formData);
  });
}

/**
 * List uploaded documents for the user
 * @param {string|null} [conversationId=null]
 */
export async function fetchDocuments(conversationId = null) {
  const query = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : '';
  return await apiRequest(`/documents${query}`);
}

/**
 * Get document metadata by ID
 * @param {string} documentId
 */
export async function getDocumentDetails(documentId) {
  return await apiRequest(`/documents/${encodeURIComponent(documentId)}`);
}

/**
 * Delete a document and its vector index
 * @param {string} documentId
 */
export async function deleteDocument(documentId) {
  return await apiRequest(`/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
  });
}

