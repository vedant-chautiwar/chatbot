/**
 * Chat API endpoints supporting synchronous calls and progressive SSE streaming
 */

import { API_BASE_URL, getAuthToken, apiRequest, ApiError } from './client';

/**
 * Send a chat message synchronously
 * @param {Object} payload
 * @param {string|null} [payload.conversationId=null]
 * @param {string} payload.message
 */
export async function sendChatMessageSync({ conversationId = null, message }) {
  return await apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
  });
}

/**
 * Stream a chat message via Server-Sent Events (SSE)
 *
 * @param {Object} params
 * @param {string|null} [params.conversationId=null]
 * @param {string} params.message
 * @param {function} [params.onMeta] Callback for { conversation_id, assistant_message_id }
 * @param {function} [params.onStatus] Callback for { status: 'thinking'|'searching'|'generating' }
 * @param {function} [params.onToken] Callback for token string delta
 * @param {function} [params.onSources] Callback for array of Source objects
 * @param {function} [params.onDone] Callback for { conversation_id, assistant_message_id, status }
 * @param {function} [params.onError] Callback for error detail
 * @param {AbortSignal} [params.signal] AbortController signal for cancellation
 */
export async function streamChatMessage({
  conversationId = null,
  message,
  onMeta,
  onStatus,
  onToken,
  onSources,
  onDone,
  onError,
  signal,
}) {
  const url = `${API_BASE_URL}/chat/stream`;
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
    signal,
  });

  if (!response.ok) {
    let errorDetail = `Stream request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      try {
        const text = await response.text();
        if (text) errorDetail = text;
      } catch {
        // Fallback
      }
    }
    throw new ApiError(errorDetail, response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete frames separated by double newline
      const frames = buffer.split('\n\n');
      // The last element is either empty (if ended with \n\n) or an incomplete frame
      buffer = frames.pop() || '';

      for (const frame of frames) {
        if (!frame.trim()) continue;

        let eventType = 'message';
        let dataStr = '';

        const lines = frame.split('\n');
        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.replace('event:', '').trim();
          } else if (line.startsWith('data:')) {
            // Append data (in case data spans multiple lines)
            const content = line.replace('data:', '').trim();
            dataStr = dataStr ? `${dataStr}\n${content}` : content;
          }
        }

        if (!dataStr) continue;

        let parsedData = null;
        try {
          parsedData = JSON.parse(dataStr);
        } catch {
          parsedData = dataStr;
        }

        switch (eventType) {
          case 'meta':
            onMeta?.(parsedData);
            break;
          case 'status':
            onStatus?.(parsedData);
            break;
          case 'token':
            if (typeof parsedData === 'object' && parsedData?.token) {
              onToken?.(parsedData.token);
            } else if (typeof parsedData === 'string') {
              onToken?.(parsedData);
            }
            break;
          case 'sources':
            if (parsedData?.sources) {
              onSources?.(parsedData.sources);
            } else if (Array.isArray(parsedData)) {
              onSources?.(parsedData);
            }
            break;
          case 'done':
            onDone?.(parsedData);
            break;
          case 'error':
            onError?.(parsedData);
            break;
          default:
            break;
        }
      }
    }

    // Flush any leftover in buffer
    if (buffer.trim()) {
      const lines = buffer.split('\n');
      let eventType = '';
      let dataStr = '';
      for (const line of lines) {
        if (line.startsWith('event:')) eventType = line.replace('event:', '').trim();
        if (line.startsWith('data:')) dataStr = line.replace('data:', '').trim();
      }
      if (eventType && dataStr) {
        try {
          const parsed = JSON.parse(dataStr);
          if (eventType === 'done') onDone?.(parsed);
          else if (eventType === 'token') onToken?.(parsed.token);
        } catch {
          // ignore
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      // User aborted stream
      return;
    }
    throw err;
  }
}
