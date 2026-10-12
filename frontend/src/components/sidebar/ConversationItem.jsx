import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, Pencil, Trash2, Check, X } from 'lucide-react';
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

  return (
    <div
      className={`group relative flex items-center justify-between w-full px-2.5 py-2 rounded-lg cursor-pointer text-sm transition-colors duration-150 ${
        isActive
          ? 'bg-[#212121] text-white font-medium'
          : 'text-[#b4b4b4] hover:text-[#ececec] hover:bg-[#171717]'
      } ${deleteLoading ? 'opacity-50 pointer-events-none' : ''}`}
      onClick={() => !isRenaming && onClick?.()}
      title={conversation.title}
    >
      <div className="flex-1 min-w-0 pr-1">
        {isRenaming ? (
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <input
              ref={renameInputRef}
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={handleRenameKeyDown}
              disabled={renameLoading}
              className="flex-1 min-w-0 px-2 py-0.5 bg-[#171717] border border-[#404040] rounded text-xs text-white focus:outline-none focus:border-gray-300"
            />
            <button
              type="button"
              onClick={handleRenameSubmit}
              disabled={renameLoading}
              className="p-1 hover:text-emerald-400 text-gray-300"
              title="Save"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setIsRenaming(false)}
              className="p-1 hover:text-red-400 text-gray-400"
              title="Cancel"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <span className="block truncate text-[13.5px] leading-snug">
            {conversation.title}
          </span>
        )}
      </div>

      {/* Context menu trigger (subtle hover state like ChatGPT) */}
      {!isRenaming && (
        <div className="relative flex-shrink-0" ref={menuRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu((v) => !v);
            }}
            className={`p-1 rounded text-gray-400 hover:text-white hover:bg-[#2e2e2e] transition-colors ${
              showMenu ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            }`}
            title="Options"
          >
            <MoreHorizontal className="w-3.5 h-3.5" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-6 z-50 min-w-[130px] bg-[#1c1c1c] border border-[#2e2e2e] rounded-xl py-1 shadow-2xl shadow-black/80 animate-fade-in text-xs">
              <button
                type="button"
                onClick={handleStartRename}
                className="w-full text-left px-3 py-1.5 text-gray-200 hover:bg-[#282828] hover:text-white flex items-center gap-2 transition-colors"
              >
                <Pencil className="w-3.5 h-3.5 text-gray-400" />
                Rename
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="w-full text-left px-3 py-1.5 text-red-400 hover:bg-red-950/30 hover:text-red-300 flex items-center gap-2 transition-colors"
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

