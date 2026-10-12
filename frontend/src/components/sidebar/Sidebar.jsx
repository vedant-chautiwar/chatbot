import React, { useState, useEffect, useCallback } from 'react';
import { Bot, SquarePen, Plus, LogOut, Search, X, PanelLeft, ChevronLeft, AlertCircle, Loader2 } from 'lucide-react';
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
  const [showSearch, setShowSearch] = useState(false);
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

  // Group conversations: Today, Previous 7 Days, Older
  const grouped = groupByRecency(filteredConversations);

  const userEmail = user?.email || user?.user_metadata?.email || 'User';
  const userName = user?.name || (userEmail.includes('@') ? userEmail.split('@')[0] : userEmail);
  const userInitials = (userName.slice(0, 2) || 'VC').toUpperCase();

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/70 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed md:relative inset-y-0 left-0 z-40 w-[260px] flex-shrink-0 bg-[#0d0d0d] border-r border-[#212121] flex flex-col h-full transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:-translate-x-full md:!w-0 md:!p-0 md:!border-r-0 overflow-hidden'
        }`}
      >
        {/* Top Header: Brand + Controls */}
        <div className="flex items-center justify-between px-3.5 py-3 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#1f1f1f] border border-[#2e2e2e] flex items-center justify-center text-white flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-[14.5px] text-[#f5f5f5] tracking-tight">
              CHAUTIBOT
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setShowSearch((v) => !v)}
              className="p-1.5 rounded-lg hover:bg-[#212121] text-[#8e8e8e] hover:text-[#ececec] transition-colors"
              title="Search chats"
            >
              <Search className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-[#212121] text-[#8e8e8e] hover:text-[#ececec] transition-colors"
              title="Close sidebar"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="px-2.5 pt-1 pb-2 flex-shrink-0">
          <button
            type="button"
            onClick={() => {
              onNewChat?.();
              if (window.innerWidth < 768) onClose?.();
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-[#ececec] hover:bg-[#212121] transition-colors font-medium text-left"
          >
            <SquarePen className="w-4 h-4 text-[#a3a3a3]" />
            <span>New chat</span>
          </button>
        </div>

        {/* Search Input (conditionally visible or toggleable) */}
        {showSearch && (
          <div className="px-2.5 pb-2 flex-shrink-0 animate-fade-in">
            <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#171717] border border-[#2a2a2a] text-xs focus-within:border-[#404040] transition-colors">
              <Search className="w-3.5 h-3.5 text-[#737373] flex-shrink-0" />
              <input
                type="search"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
                className="flex-1 bg-transparent text-[#ececec] placeholder-[#737373] text-xs focus:outline-none"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="text-[#737373] hover:text-[#ececec]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-2 pb-2 min-h-0">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-10 gap-2 text-[#737373]">
              <Loader2 className="w-4 h-4 animate-spin text-[#a3a3a3]" />
              <span className="text-xs">Loading conversations...</span>
            </div>
          ) : error ? (
            <div className="mx-1 mt-2 p-2.5 rounded-lg bg-[#141414] border border-[#262626] text-xs text-[#a3a3a3] flex items-start gap-2">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-red-400" />
              <div>
                <p className="font-medium text-[#d4d4d8]">Failed to load</p>
                <p className="text-[#8e8e8e] mt-0.5 leading-relaxed text-[11px]">{error}</p>
                <button
                  type="button"
                  onClick={loadConversations}
                  className="mt-1 text-xs text-[#d4d4d8] hover:text-white underline"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center px-3">
              <p className="text-xs text-[#737373]">
                {searchQuery ? 'No matching conversations' : 'No conversations yet'}
              </p>
            </div>
          ) : (
            <div className="space-y-4 py-1">
              {grouped.map(({ label, items }) =>
                items.length > 0 ? (
                  <div key={label}>
                    <p className="px-2.5 py-1 text-[11px] font-medium text-[#8e8e8e] tracking-tight">
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
                            if (window.innerWidth < 768) onClose?.();
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

        {/* Account Profile Section */}
        <div className="flex-shrink-0 border-t border-[#212121] p-2">
          <div className="flex items-center justify-between p-2 rounded-lg hover:bg-[#171717] transition-colors group">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-[#c2410c] flex items-center justify-center text-xs font-semibold text-white flex-shrink-0 shadow-sm">
                {userInitials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-[#ececec] truncate leading-tight">
                  {userName}
                </p>
                <p className="text-[11px] text-[#737373] truncate leading-tight mt-0.5">
                  Free
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              className="p-1.5 rounded-lg text-[#737373] hover:text-red-400 hover:bg-[#262626] transition-colors disabled:opacity-50"
              title="Sign out"
            >
              {loggingOut ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <LogOut className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

// Group conversations into Recents or Today / Previous 7 Days / Older
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
    { label: 'Previous 7 Days', items: thisWeek },
    { label: 'Older', items: older },
  ];
}

