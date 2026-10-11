import React, { useState, useEffect, useCallback } from 'react';
import { Bot, Plus, LogOut, Search, X, User, ChevronLeft, AlertCircle, Loader2, MessageSquare } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { fetchConversations } from '../../api/conversations';
import { ConversationItem } from './ConversationItem';

export function Sidebar({
  isOpen,
  onClose,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  refreshTrigger,
}) {
  const { user, logout } = useAuth();

  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);

  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchConversations({ limit: 50 });
      setConversations(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load conversations.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load + refresh when refreshTrigger changes
  useEffect(() => {
    loadConversations();
  }, [loadConversations, refreshTrigger]);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      setLoggingOut(false);
    }
  };

  const handleRenamed = (updated) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === updated.id ? { ...c, title: updated.title } : c))
    );
  };

  const handleDeleted = (deletedId) => {
    setConversations((prev) => prev.filter((c) => c.id !== deletedId));
    if (activeConversationId === deletedId) {
      onNewChat?.();
    }
  };

  // Filter conversations by search query
  const filteredConversations = searchQuery.trim()
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.last_message_preview || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : conversations;

  // Group conversations by recency: Today, This Week, Older
  const grouped = groupByRecency(filteredConversations);

  const userDisplay = user?.email || user?.user_metadata?.email || 'User';
  const userInitial = (userDisplay[0] || 'U').toUpperCase();

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed md:relative inset-y-0 left-0 z-30 w-64 flex-shrink-0 bg-chat-sidebar border-r border-chat-border flex flex-col h-full transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-3 border-b border-chat-border flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-sm flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <span className="font-semibold text-[15px] text-white tracking-tight">CHAUTIBOT</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="md:hidden p-1.5 rounded-lg hover:bg-chat-surface text-gray-400 hover:text-gray-200 transition-colors"
            title="Close sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-2.5 pt-3 pb-2 flex-shrink-0">
          <button
            type="button"
            onClick={() => { onNewChat?.(); onClose?.(); }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-brand-600/10 hover:bg-brand-600/20 border border-brand-600/25 hover:border-brand-500/40 text-brand-400 hover:text-brand-300 text-sm font-medium transition-all duration-150"
          >
            <Plus className="w-4 h-4" />
            New chat
          </button>
        </div>

        {/* Search */}
        <div className="px-2.5 pb-2 flex-shrink-0">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-chat-surface border border-chat-border text-sm focus-within:border-brand-500/50 transition-colors">
            <Search className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
            <input
              type="search"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-transparent text-gray-200 placeholder-gray-500 text-xs focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="text-gray-500 hover:text-gray-300 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto px-2 pb-2 min-h-0">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-10 gap-2 text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin text-brand-400" />
              <span className="text-xs">Loading conversations...</span>
            </div>
          ) : error ? (
            <div className="mx-1 mt-2 p-3 rounded-xl bg-red-950/30 border border-red-800/30 text-xs text-red-300 flex items-start gap-2">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-red-400" />
              <div>
                <p className="font-medium">Failed to load</p>
                <p className="text-red-400/80 mt-0.5">{error}</p>
                <button
                  type="button"
                  onClick={loadConversations}
                  className="mt-1.5 text-brand-400 hover:text-brand-300 font-medium underline"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 gap-1.5 text-gray-500 text-center px-3">
              <MessageSquare className="w-8 h-8 text-gray-700 mb-1" />
              <p className="text-xs font-medium text-gray-400">
                {searchQuery ? 'No matching conversations' : 'No conversations yet'}
              </p>
              <p className="text-[11px] text-gray-600">
                {searchQuery ? 'Try a different search' : 'Start a new chat above'}
              </p>
            </div>
          ) : (
            <div className="space-y-1 py-1">
              {grouped.map(({ label, items }) =>
                items.length > 0 ? (
                  <div key={label}>
                    <p className="px-2 py-1 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                      {label}
                    </p>
                    <div className="space-y-0.5">
                      {items.map((conv) => (
                        <ConversationItem
                          key={conv.id}
                          conversation={conv}
                          isActive={conv.id === activeConversationId}
                          onClick={() => {
                            onSelectConversation?.(conv.id);
                            onClose?.();
                          }}
                          onRenamed={handleRenamed}
                          onDeleted={handleDeleted}
                        />
                      ))}
                    </div>
                  </div>
                ) : null
              )}
            </div>
          )}
        </div>

        {/* Account area */}
        <div className="flex-shrink-0 border-t border-chat-border px-2.5 py-2.5 space-y-1">
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-xl">
            <div className="w-7 h-7 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center text-xs font-semibold text-gray-200 flex-shrink-0">
              {userInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-200 truncate">{userDisplay}</p>
              <p className="text-[10px] text-gray-500">Authenticated user</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="w-full flex items-center gap-2 px-2.5 py-2 rounded-xl text-gray-400 hover:text-red-300 hover:bg-red-950/20 text-xs font-medium transition-colors disabled:opacity-50"
          >
            {loggingOut ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <LogOut className="w-3.5 h-3.5" />
            )}
            <span>{loggingOut ? 'Signing out...' : 'Sign out'}</span>
          </button>
        </div>
      </aside>
    </>
  );
}

// Group conversations by time into Today, This Week, Older
function groupByRecency(conversations) {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const weekStart = new Date(todayStart);
  weekStart.setDate(weekStart.getDate() - 7);

  const today = [];
  const thisWeek = [];
  const older = [];

  for (const conv of conversations) {
    const updatedAt = new Date(conv.updated_at || conv.created_at);
    if (updatedAt >= todayStart) {
      today.push(conv);
    } else if (updatedAt >= weekStart) {
      thisWeek.push(conv);
    } else {
      older.push(conv);
    }
  }

  return [
    { label: 'Today', items: today },
    { label: 'This Week', items: thisWeek },
    { label: 'Older', items: older },
  ];
}
