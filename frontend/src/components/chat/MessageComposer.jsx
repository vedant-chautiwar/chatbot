import React, { useRef, useEffect, useState } from 'react';
import { ArrowUp, Square, Paperclip, X, FileText, FileCode, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const ALLOWED_EXTENSIONS = [
  '.pdf', '.txt', '.md',
  '.py', '.c', '.cpp', '.h', '.hpp', '.java',
  '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.sql'
];

const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15 MB

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function isCodeFile(filename) {
  const codeExts = ['.py', '.c', '.cpp', '.h', '.hpp', '.java', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.sql'];
  const ext = (filename || '').toLowerCase().slice((filename || '').lastIndexOf('.'));
  return codeExts.includes(ext);
}

export function MessageComposer({
  input,
  setInput,
  onSendMessage,
  onStopStreaming,
  isStreaming,
  isLoading,
  attachment = null,
  onFileSelect = null,
  onRemoveAttachment = null,
  isUploading = false,
}) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState(null);

  // Auto-resize textarea height up to 200px
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const nextHeight = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = `${Math.max(nextHeight, 44)}px`;
  }, [input]);

  const handleValidateAndSelect = (file) => {
    setLocalError(null);
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setLocalError(`Unsupported file type (${ext}). Supported: PDF, TXT, MD, and source code files.`);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setLocalError('File exceeds 15 MB maximum size limit.');
      return;
    }

    onFileSelect?.(file);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleValidateAndSelect(file);
    }
    // Reset file input so selecting the same file triggers change
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleValidateAndSelect(file);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && !isLoading && !isUploading && (input.trim() || attachment)) {
        onSendMessage();
      }
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (isStreaming) {
      onStopStreaming?.();
    } else if (!isLoading && !isUploading && (input.trim() || attachment)) {
      onSendMessage();
    }
  };

  const canSend = !isLoading && !isStreaming && !isUploading && (input.trim().length > 0 || (attachment && attachment.status === 'ready'));

  return (
    <div className="w-full max-w-[740px] mx-auto px-4 sm:px-6 pb-4 pt-1">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept={ALLOWED_EXTENSIONS.join(',')}
        className="hidden"
      />

      {/* Local validation error toast */}
      {localError && (
        <div className="mb-2 p-2 rounded-xl bg-red-950/40 border border-red-800/40 flex items-center justify-between text-xs text-red-200 animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
            <span>{localError}</span>
          </div>
          <button
            type="button"
            onClick={() => setLocalError(null)}
            className="text-red-400 hover:text-white px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Attachment Preview Card */}
      {attachment && (
        <div className="mb-2 p-2.5 px-3 rounded-2xl bg-[#1e1e1e] border border-[#383838] flex items-center justify-between gap-3 text-xs text-[#ececec] animate-fade-in">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-1.5 rounded-lg bg-[#2a2a2a] text-[#a3a3a3] flex-shrink-0">
              {isCodeFile(attachment.filename) ? (
                <FileCode className="w-4 h-4 text-emerald-400" />
              ) : (
                <FileText className="w-4 h-4 text-blue-400" />
              )}
            </div>
            <div className="min-w-0">
              <p className="font-medium truncate max-w-[240px] sm:max-w-md text-[#ececec]">
                {attachment.filename}
              </p>
              <div className="flex items-center gap-2 text-[11px] text-[#8e8e8e] mt-0.5">
                <span>{formatFileSize(attachment.size)}</span>
                <span>•</span>
                {attachment.status === 'uploading' ? (
                  <span className="flex items-center gap-1 text-blue-400">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Uploading {attachment.progress || 0}%...
                  </span>
                ) : attachment.status === 'failed' ? (
                  <span className="flex items-center gap-1 text-red-400">
                    <AlertCircle className="w-3 h-3" />
                    Upload failed
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-emerald-400">
                    <CheckCircle2 className="w-3 h-3" />
                    Ready for analysis
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onRemoveAttachment}
            disabled={isUploading}
            className="p-1 rounded-full text-[#8e8e8e] hover:text-white hover:bg-[#2c2c2c] transition-colors flex-shrink-0"
            title="Remove attachment"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Composer Box */}
      <form
        onSubmit={handleFormSubmit}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex items-end gap-2 bg-[#2f2f2f] border transition-all duration-150 rounded-[28px] p-2 sm:p-2.5 shadow-lg ${
          isDragging
            ? 'border-blue-500 bg-[#333333]'
            : 'border-transparent focus-within:border-[#444444]'
        }`}
      >
        {/* Attachment Paperclip button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || isStreaming || isUploading}
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-[#a3a3a3] hover:text-white hover:bg-[#3a3a3a] transition-colors mb-0.5 ml-0.5 disabled:opacity-40"
          title="Attach document or code file (.pdf, .txt, .md, .py, .cpp, .js, etc.)"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={attachment ? "Ask questions about this file..." : "Ask anything, paste code, or attach a document..."}
          rows={1}
          disabled={isLoading && !isStreaming}
          className="flex-1 min-w-0 py-1.5 px-1 bg-transparent text-[#ececec] placeholder-[#8e8e8e] text-[15px] resize-none focus:outline-none disabled:opacity-50 max-h-[200px] overflow-y-auto leading-relaxed"
        />

        {/* Action Button: Send or Stop */}
        <div className="flex-shrink-0 mb-0.5 mr-0.5">
          {isStreaming ? (
            <button
              type="button"
              onClick={onStopStreaming}
              className="w-8 h-8 rounded-full bg-white text-black hover:bg-[#e5e5e5] flex items-center justify-center transition-colors shadow-sm"
              title="Stop generating"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!canSend}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-150 ${
                canSend
                  ? 'bg-white text-black hover:bg-[#e5e5e5] shadow-sm active:scale-95'
                  : 'bg-[#424242] text-[#686868] cursor-not-allowed'
              }`}
              title="Send message"
            >
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            </button>
          )}
        </div>
      </form>

      {/* Footer disclaimer */}
      <div className="text-center mt-2.5 text-[12px] text-[#636363] tracking-normal">
        CHAUTIBOT can make mistakes. Verify important information.
      </div>
    </div>
  );
}
