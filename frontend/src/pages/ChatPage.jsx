import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { ChatMessage } from '../components/chat/ChatMessage';
import { MessageComposer } from '../components/chat/MessageComposer';
import { WelcomeScreen } from '../components/chat/WelcomeScreen';
import { Sidebar } from '../components/sidebar/Sidebar';
import { fetchConversationDetails } from '../api/conversations';
import { streamChatMessage } from '../api/chat';
import { PanelLeft, Bot } from 'lucide-react';

const SCROLL_THRESHOLD = 100; // px from bottom to auto-scroll

export function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState(null);
  const [streamStatus, setStreamStatus] = useState(null);
  const [conversationTitle, setConversationTitle] = useState('');
  const [sidebarRefresh, setSidebarRefresh] = useState(0);

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const streamingMessageIdRef = useRef(null);
  const userScrolledUpRef = useRef(false);

  // Close sidebar by default on mobile
  useEffect(() => {
    const isMobile = window.innerWidth < 768;
    setSidebarOpen(!isMobile);
  }, []);

  // Track whether the user manually scrolled up (to avoid forcing scroll during read)
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    userScrolledUpRef.current = distanceFromBottom > SCROLL_THRESHOLD;
  }, []);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback((force = false) => {
    if (force || !userScrolledUpRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  // Scroll to bottom on new messages if user isn't scrolled up
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load conversation messages when switching conversations
  const loadConversation = useCallback(async (convId) => {
    if (!convId) return;
    setMessagesLoading(true);
    setMessagesError(null);
    setMessages([]);
    setConversationTitle('');
    userScrolledUpRef.current = false;
    try {
      const data = await fetchConversationDetails(convId);
      setConversationTitle(data.conversation?.title || '');
      setMessages(data.messages || []);
    } catch (err) {
      setMessagesError(err.message || 'Failed to load conversation.');
    } finally {
      setMessagesLoading(false);
      // Scroll to bottom after loading
      setTimeout(() => scrollToBottom(true), 100);
    }
  }, [scrollToBottom]);

  const handleSelectConversation = useCallback((convId) => {
    if (convId === activeConversationId) return;
    // Stop any current streaming
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setStreamStatus(null);
    setActiveConversationId(convId);
    loadConversation(convId);
  }, [activeConversationId, loadConversation]);

  const handleNewChat = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setStreamStatus(null);
    setActiveConversationId(null);
    setMessages([]);
    setConversationTitle('');
    setMessagesError(null);
    userScrolledUpRef.current = false;
  }, []);

  const handleSendMessage = useCallback(async (overrideMessage) => {
    const messageText = (overrideMessage || input).trim();
    if (!messageText || isStreaming || isLoading) return;

    setInput('');
    setMessagesError(null);
    userScrolledUpRef.current = false;

    // Append user message immediately to UI
    const tempUserMsgId = `user-${Date.now()}`;
    const userMessage = {
      id: tempUserMsgId,
      role: 'user',
      content: messageText,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    scrollToBottom(true);

    // Append a placeholder streaming assistant message
    const tempAssistantId = `assistant-stream-${Date.now()}`;
    streamingMessageIdRef.current = tempAssistantId;

    const streamingPlaceholder = {
      id: tempAssistantId,
      role: 'assistant',
      content: '',
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, streamingPlaceholder]);

    setIsStreaming(true);
    setIsLoading(true);
    setStreamStatus('thinking');

    // Create an AbortController to allow cancellation
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let resolvedConversationId = activeConversationId;

    try {
      await streamChatMessage({
        conversationId: activeConversationId,
        message: messageText,
        signal: controller.signal,
        onMeta: (meta) => {
          // Backend confirmed conversation ID (may be new)
          if (meta.conversation_id && meta.conversation_id !== activeConversationId) {
            resolvedConversationId = meta.conversation_id;
            setActiveConversationId(meta.conversation_id);
          }
          if (meta.title) {
            setConversationTitle(meta.title);
            setSidebarRefresh((n) => n + 1);
          }
        },
        onStatus: (data) => {
          setStreamStatus(data.status);
        },
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingMessageIdRef.current
                ? { ...m, content: m.content + token }
                : m
            )
          );
          scrollToBottom();
        },
        onSources: (sources) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingMessageIdRef.current
                ? { ...m, sources: sources || [] }
                : m
            )
          );
        },
        onDone: (data) => {
          // Finalize the streaming message
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingMessageIdRef.current
                ? { ...m, status: 'completed' }
                : m
            )
          );
          setIsStreaming(false);
          setIsLoading(false);
          setStreamStatus(null);
          // Trigger sidebar refresh to show new / updated conversation
          setSidebarRefresh((n) => n + 1);
          scrollToBottom(true);
        },
        onError: (err) => {
          const errorDetail = typeof err === 'string' ? err : err?.detail || 'An error occurred during streaming.';
          setMessages((prev) => {
            const streamMsg = prev.find((m) => m.id === streamingMessageIdRef.current);
            if (!streamMsg || !streamMsg.content) {
              // Remove empty error placeholder without content
              return prev.filter((m) => m.id !== streamingMessageIdRef.current);
            }
            return prev.map((m) =>
              m.id === streamingMessageIdRef.current
                ? { ...m, content: m.content || '', error: errorDetail }
                : m
            );
          });
          setMessagesError(errorDetail);
          setIsStreaming(false);
          setIsLoading(false);
          setStreamStatus(null);
        },
      });
    } catch (err) {
      if (err.name === 'AbortError') {
        // Streaming was intentionally aborted by user
        setIsStreaming(false);
        setIsLoading(false);
        setStreamStatus(null);
        setSidebarRefresh((n) => n + 1);
        return;
      }
      console.error('Streaming error:', err);
      setMessagesError(err.message || 'Failed to send message. Please try again.');
      // Remove empty streaming placeholder
      setMessages((prev) => {
        const streamMsg = prev.find((m) => m.id === streamingMessageIdRef.current);
        if (streamMsg && !streamMsg.content) {
          return prev.filter((m) => m.id !== streamingMessageIdRef.current);
        }
        return prev;
      });
      // Put the draft message back in the composer
      setInput(messageText);
      setIsStreaming(false);
      setIsLoading(false);
      setStreamStatus(null);
    }
  }, [input, isStreaming, isLoading, activeConversationId, scrollToBottom]);

  const handleStopStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setStreamStatus(null);
    setSidebarRefresh((n) => n + 1);
  }, []);

  const handleWelcomePrompt = useCallback((prompt) => {
    setInput('');
    handleSendMessage(prompt);
  }, [handleSendMessage]);

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-chat-bg">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        refreshTrigger={sidebarRefresh}
      />

      {/* Main chat area */}
      <div
        className={`flex flex-col flex-1 min-w-0 h-full transition-all duration-200 ${
          sidebarOpen ? 'md:ml-0' : ''
        }`}
      >
        {/* Top Header */}
        <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-chat-border bg-chat-bg/80 backdrop-blur-sm">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setSidebarOpen((v) => !v)}
              className="p-2 rounded-xl hover:bg-chat-surface text-gray-400 hover:text-gray-200 transition-colors flex-shrink-0"
              title="Toggle sidebar"
            >
              <PanelLeft className="w-4.5 h-4.5 w-[18px] h-[18px]" />
            </button>

            {!sidebarOpen && (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <span className="text-sm font-semibold text-white">CHAUTIBOT</span>
              </div>
            )}

            {conversationTitle && (
              <span className="text-sm text-gray-300 truncate font-medium" title={conversationTitle}>
                {conversationTitle}
              </span>
            )}
          </div>
        </header>

        {/* Messages area */}
        <div
          className="flex-1 overflow-y-auto relative"
          ref={messagesContainerRef}
          onScroll={handleScroll}
        >
          {messagesLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3 text-gray-400">
                <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
                <span className="text-sm">Loading conversation...</span>
              </div>
            </div>
          ) : messagesError && messages.length === 0 ? (
            <div className="flex items-center justify-center h-full p-6">
              <div className="max-w-sm text-center space-y-3">
                <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
                <h3 className="text-base font-semibold text-gray-200">Failed to load conversation</h3>
                <p className="text-sm text-gray-400">{messagesError}</p>
                <button
                  type="button"
                  onClick={() => activeConversationId && loadConversation(activeConversationId)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Retry
                </button>
              </div>
            </div>
          ) : !hasMessages ? (
            <WelcomeScreen onSelectPrompt={handleWelcomePrompt} />
          ) : (
            <div className="pb-4 pt-2">
              {messages.map((msg, idx) => {
                const isLastMessage = idx === messages.length - 1;
                const isStreamingThis = isStreaming && isLastMessage && msg.role === 'assistant';
                return (
                  <ChatMessage
                    key={msg.id || idx}
                    message={msg}
                    isStreaming={isStreamingThis}
                    streamStatus={isStreamingThis ? streamStatus : null}
                  />
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error banner at bottom if send fails */}
        {messagesError && hasMessages && (
          <div className="flex-shrink-0 mx-4 mb-2 p-2.5 rounded-xl bg-red-950/40 border border-red-800/40 flex items-center gap-2 text-xs text-red-200 animate-fade-in">
            <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
            <span className="flex-1">{messagesError}</span>
            <button
              type="button"
              onClick={() => setMessagesError(null)}
              className="text-red-400 hover:text-red-200"
            >
              ✕
            </button>
          </div>
        )}

        {/* Message composer */}
        <div className="flex-shrink-0 pb-2 pt-1 bg-chat-bg">
          <MessageComposer
            input={input}
            setInput={setInput}
            onSendMessage={handleSendMessage}
            onStopStreaming={handleStopStreaming}
            isStreaming={isStreaming}
            isLoading={isLoading && !isStreaming}
          />
        </div>
      </div>
    </div>
  );
}
