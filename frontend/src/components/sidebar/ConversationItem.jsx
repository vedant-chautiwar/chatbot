import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, Pencil, Trash2, Check, X, MessageSquare } from 'lucide-react';
import { renameConversation, deleteConversation } from '../../api/conversations';

export function ConversationItem({
  conversation,
  isActive,
  onClick,
  onRenamed,
  onDeleted,
}) {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(conversation.title);
  const [renameLoading, setRenameLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const menuRef = useRef(null);
  const renameInputRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    if (!showMenu) return;
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showMenu]);

  // Focus rename input when entering rename mode
  useEffect(() => {
    if (isRenaming && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [isRenaming]);

  const handleStartRename = (e) => {
    e.stopPropagation();
    setRenameValue(conversation.title);
    setShowMenu(false);
    setIsRenaming(true);
  };

  const handleRenameSubmit = async () => {
    const trimmed = renameValue.trim();
    if (!trimmed || trimmed === conversation.title) {
      setIsRenaming(false);
      return;
    }
    setRenameLoading(true);
    try {
      const updated = await renameConversation(conversation.id, trimmed);
      onRenamed?.(updated);
      setIsRenaming(false);
    } catch (err) {
      console.error('Failed to rename conversation:', err);
    } finally {
      setRenameLoading(false);
    }
  };

  const handleRenameKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      setIsRenaming(false);
    }
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    setShowMenu(false);
    if (!window.confirm(`Delete "${conversation.title}"? This cannot be undone.`)) return;
    setDeleteLoading(true);
    try {
      await deleteConversation(conversation.id);
      onDeleted?.(conversation.id);
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    } finally {
      setDeleteLoading(false);
    }
  };

  const preview = conversation.last_message_preview;
  const messageCount = conversation.message_count || 0;

  return (
    <div
      className={`group relative flex items-start gap-2 w-full px-2.5 py-2.5 rounded-xl cursor-pointer transition-all duration-100 ${
        isActive
          ? 'bg-chat-surfaceHover border border-chat-border text-white'
          : 'hover:bg-chat-surfaceHover/60 text-gray-400 hover:text-gray-200 border border-transparent'
      } ${deleteLoading ? 'opacity-50 pointer-events-none' : ''}`}
      onClick={() => !isRenaming && onClick?.()}
      title={conversation.title}
    >
      <div className="flex-shrink-0 mt-0.5">
        <MessageSquare className={`w-3.5 h-3.5 ${isActive ? 'text-brand-400' : 'text-gray-500 group-hover:text-gray-400'}`} />
      </div>

      <div className="flex-1 min-w-0">
        {isRenaming ? (
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <input
              ref={renameInputRef}
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={handleRenameKeyDown}
              disabled={renameLoading}
              className="flex-1 min-w-0 px-1.5 py-0.5 bg-chat-elevated border border-brand-500 rounded text-xs text-white focus:outline-none"
            />
            <button
              type="button"
              onClick={handleRenameSubmit}
              disabled={renameLoading}
              className="p-1 hover:text-emerald-400 text-gray-300"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setIsRenaming(false)}
              className="p-1 hover:text-red-400 text-gray-400"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <>
            <p className="text-xs font-medium leading-snug truncate text-gray-200">
              {conversation.title}
            </p>
            {preview && (
              <p className="text-[11px] text-gray-500 truncate mt-0.5 leading-tight">
                {preview}
              </p>
            )}
          </>
        )}
      </div>

      {/* Context menu trigger */}
      {!isRenaming && (
        <div className="relative flex-shrink-0" ref={menuRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu((v) => !v);
            }}
            className={`p-1 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-chat-elevated transition-colors ${
              showMenu ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            }`}
            title="Conversation actions"
          >
            <MoreHorizontal className="w-3.5 h-3.5" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-7 z-30 min-w-[130px] bg-chat-elevated border border-chat-border rounded-xl py-1 shadow-xl shadow-black/50 animate-fade-in">
              <button
                type="button"
                onClick={handleStartRename}
                className="w-full text-left px-3 py-1.5 text-xs text-gray-200 hover:bg-chat-surfaceHover hover:text-white flex items-center gap-2 transition-colors"
              >
                <Pencil className="w-3.5 h-3.5 text-brand-400" />
                Rename
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="w-full text-left px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/30 hover:text-red-200 flex items-center gap-2 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5 text-red-400" />
                Delete
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
