import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, Loader2, RefreshCw, PanelLeft, Bot, SquarePen, ChevronDown } from 'lucide-react';
import { ChatMessage } from '../components/chat/ChatMessage';
import { MessageComposer } from '../components/chat/MessageComposer';
import { WelcomeScreen } from '../components/chat/WelcomeScreen';
import { Sidebar } from '../components/sidebar/Sidebar';
import { fetchConversationDetails } from '../api/conversations';
import { streamChatMessage } from '../api/chat';
import { uploadDocument, deleteDocument } from '../api/documents';

const SCROLL_THRESHOLD = 120; // px from bottom to show scroll button

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
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  // Document attachment state
  const [attachment, setAttachment] = useState(null);
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false);

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

  // Track whether the user manually scrolled up
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    const isScrolledUp = distanceFromBottom > SCROLL_THRESHOLD;
    userScrolledUpRef.current = isScrolledUp;
    setShowScrollBottom(isScrolledUp);
  }, []);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback((force = false) => {
    if (force || !userScrolledUpRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      setShowScrollBottom(false);
      userScrolledUpRef.current = false;
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
    setAttachment(null);
    userScrolledUpRef.current = false;
    try {
      const data = await fetchConversationDetails(convId);
      setConversationTitle(data.conversation?.title || '');
      setMessages(data.messages || []);
    } catch (err) {
      setMessagesError(err.message || 'Failed to load conversation.');
    } finally {
      setMessagesLoading(false);
      setTimeout(() => scrollToBottom(true), 100);
    }
  }, [scrollToBottom]);

  const handleSelectConversation = useCallback((convId) => {
    if (convId === activeConversationId) return;
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setStreamStatus(null);
    setAttachment(null);
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
    setAttachment(null);
    userScrolledUpRef.current = false;
  }, []);

  // Document attachment handling
  const handleFileSelect = useCallback(async (file) => {
    if (!file) return;

    setAttachment({
      file,
      filename: file.name,
      size: file.size,
      status: 'uploading',
      progress: 0,
      id: null,
    });
    setIsUploadingAttachment(true);
    setMessagesError(null);

    try {
      const res = await uploadDocument({
        file,
        conversationId: activeConversationId,
        onProgress: (pct) => {
          setAttachment((prev) => (prev ? { ...prev, progress: pct } : null));
        },
      });

      setAttachment({
        file,
        filename: res.document.filename,
        size: res.document.file_size,
        category: res.document.category,
        status: 'ready',
        progress: 100,
        id: res.document.id,
      });
    } catch (err) {
      console.error('Document upload error:', err);
      setAttachment((prev) => (prev ? { ...prev, status: 'failed', error: err.message } : null));
      setMessagesError(err.message || 'Failed to upload document.');
    } finally {
      setIsUploadingAttachment(false);
    }
  }, [activeConversationId]);

  const handleRemoveAttachment = useCallback(async () => {
    const docId = attachment?.id;
    setAttachment(null);
    setIsUploadingAttachment(false);
    if (docId) {
      try {
        await deleteDocument(docId);
      } catch {
        // non-blocking
      }
    }
  }, [attachment]);

  const handleSendMessage = useCallback(async (overrideMessage) => {
    let messageText = (overrideMessage || input).trim();
    const currentAtt = attachment;

    // If message text is blank but an attachment is attached, provide intuitive default prompt
    if (!messageText && currentAtt && currentAtt.status === 'ready') {
      messageText = `Please analyze and summarize the attached file (${currentAtt.filename}).`;
    }

    if (!messageText || isStreaming || isLoading || isUploadingAttachment) return;

    setInput('');
    setAttachment(null);
    setMessagesError(null);
    userScrolledUpRef.current = false;

    // Append user message immediately to UI
    const tempUserMsgId = `user-${Date.now()}`;
    const userMessage = {
      id: tempUserMsgId,
      role: 'user',
      content: messageText,
      attachment: currentAtt && currentAtt.status === 'ready' ? { filename: currentAtt.filename, size: currentAtt.size } : null,
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

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let resolvedConversationId = activeConversationId;
    const documentIds = currentAtt && currentAtt.id ? [currentAtt.id] : null;

    try {
      await streamChatMessage({
        conversationId: activeConversationId,
        message: messageText,
        documentIds: documentIds,
        signal: controller.signal,
        onMeta: (meta) => {
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
          setSidebarRefresh((n) => n + 1);
          scrollToBottom(true);
        },
        onError: (err) => {
          const errorDetail = typeof err === 'string' ? err : err?.detail || 'An error occurred during streaming.';
          setMessages((prev) => {
            const streamMsg = prev.find((m) => m.id === streamingMessageIdRef.current);
            if (!streamMsg || !streamMsg.content) {
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
        setIsStreaming(false);
        setIsLoading(false);
        setStreamStatus(null);
        setSidebarRefresh((n) => n + 1);
        return;
      }
      console.error('Streaming error:', err);
      setMessagesError(err.message || 'Failed to send message. Please try again.');
      setMessages((prev) => {
        const streamMsg = prev.find((m) => m.id === streamingMessageIdRef.current);
        if (streamMsg && !streamMsg.content) {
          return prev.filter((m) => m.id !== streamingMessageIdRef.current);
        }
        return prev;
      });
      setInput(messageText);
      setIsStreaming(false);
      setIsLoading(false);
      setStreamStatus(null);
    }
  }, [input, isStreaming, isLoading, isUploadingAttachment, attachment, activeConversationId, scrollToBottom]);

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
    <div className="flex h-screen w-screen overflow-hidden bg-black text-[#ececec]">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        refreshTrigger={sidebarRefresh}
      />

      {/* Main chat canvas */}
      <div className="flex flex-col flex-1 min-w-0 h-full relative bg-black">
        {/* Top Header */}
        <header className="flex-shrink-0 flex items-center justify-between px-3 sm:px-4 py-2.5 bg-black z-10 min-h-[48px]">
          <div className="flex items-center gap-2 min-w-0">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="p-1.5 rounded-lg hover:bg-[#212121] text-[#a3a3a3] hover:text-[#ececec] transition-colors flex-shrink-0"
                title="Open sidebar"
              >
                <PanelLeft className="w-[18px] h-[18px]" />
              </button>
            )}

            {!sidebarOpen && (
              <button
                type="button"
                onClick={handleNewChat}
                className="p-1.5 rounded-lg hover:bg-[#212121] text-[#a3a3a3] hover:text-[#ececec] transition-colors flex-shrink-0"
                title="New chat"
              >
                <SquarePen className="w-[18px] h-[18px]" />
              </button>
            )}

            <div className="flex items-center gap-2 min-w-0 ml-0.5">
              {!sidebarOpen && (
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="w-6 h-6 rounded-md bg-[#1f1f1f] border border-[#2e2e2e] flex items-center justify-center text-white">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm font-semibold text-white tracking-tight">CHAUTIBOT</span>
                </div>
              )}

              {conversationTitle && (
                <span className="text-sm text-[#ececec] truncate font-medium max-w-xs sm:max-w-md" title={conversationTitle}>
                  {conversationTitle}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {sidebarOpen && (
              <button
                type="button"
                onClick={handleNewChat}
                className="p-1.5 rounded-lg hover:bg-[#212121] text-[#a3a3a3] hover:text-[#ececec] transition-colors flex-shrink-0"
                title="New chat"
              >
                <SquarePen className="w-[18px] h-[18px]" />
              </button>
            )}
          </div>
        </header>

        {/* Messages area */}
        <div
          className="flex-1 min-h-0 overflow-y-auto relative"
          ref={messagesContainerRef}
          onScroll={handleScroll}
        >
          {messagesLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3 text-[#737373]">
                <Loader2 className="w-5 h-5 animate-spin text-[#a3a3a3]" />
                <span className="text-xs">Loading conversation...</span>
              </div>
            </div>
          ) : messagesError && messages.length === 0 ? (
            <div className="flex items-center justify-center h-full p-6">
              <div className="max-w-sm text-center space-y-3">
                <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
                <h3 className="text-sm font-semibold text-gray-200">Failed to load conversation</h3>
                <p className="text-xs text-[#a3a3a3]">{messagesError}</p>
                <button
                  type="button"
                  onClick={() => activeConversationId && loadConversation(activeConversationId)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#212121] hover:bg-[#2a2a2a] text-white text-xs font-medium transition-colors border border-[#333333]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Retry
                </button>
              </div>
            </div>
          ) : !hasMessages ? (
            <WelcomeScreen onSelectPrompt={handleWelcomePrompt} />
          ) : (
            <div className="pb-6 pt-3">
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

        {/* Scroll down floating button */}
        {showScrollBottom && hasMessages && (
          <button
            type="button"
            onClick={() => scrollToBottom(true)}
            className="absolute bottom-28 left-1/2 -translate-x-1/2 z-20 w-8 h-8 rounded-full bg-[#212121] border border-[#383838] hover:bg-[#2e2e2e] text-[#ececec] flex items-center justify-center shadow-lg transition-all animate-fade-in"
            title="Scroll to bottom"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        )}

        {/* Error banner if send fails */}
        {messagesError && hasMessages && (
          <div className="flex-shrink-0 max-w-3xl mx-auto w-full px-4 mb-2">
            <div className="p-2.5 rounded-xl bg-red-950/30 border border-red-800/40 flex items-center gap-2 text-xs text-red-200 animate-fade-in">
              <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
              <span className="flex-1">{messagesError}</span>
              <button
                type="button"
                onClick={() => setMessagesError(null)}
                className="text-red-400 hover:text-red-200 px-1"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Message composer */}
        <div className="flex-shrink-0 bg-black">
          <MessageComposer
            input={input}
            setInput={setInput}
            onSendMessage={handleSendMessage}
            onStopStreaming={handleStopStreaming}
            isStreaming={isStreaming}
            isLoading={isLoading && !isStreaming}
            attachment={attachment}
            onFileSelect={handleFileSelect}
            onRemoveAttachment={handleRemoveAttachment}
            isUploading={isUploadingAttachment}
          />
        </div>
      </div>
    </div>
  );
}
