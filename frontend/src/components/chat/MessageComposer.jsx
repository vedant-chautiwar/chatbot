import React, { useRef, useEffect } from 'react';
import { ArrowUp, Square } from 'lucide-react';

export function MessageComposer({
  input,
  setInput,
  onSendMessage,
  onStopStreaming,
  isStreaming,
  isLoading,
}) {
  const textareaRef = useRef(null);

  // Auto-resize textarea height up to 200px
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const nextHeight = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = `${Math.max(nextHeight, 48)}px`;
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && !isLoading && input.trim()) {
        onSendMessage();
      }
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (isStreaming) {
      onStopStreaming?.();
    } else if (!isLoading && input.trim()) {
      onSendMessage();
    }
  };

  const canSend = !isLoading && !isStreaming && input.trim().length > 0;

  return (
    <div className="w-full max-w-3xl mx-auto px-4 sm:px-6 pb-4 pt-1">
      <form
        onSubmit={handleFormSubmit}
        className="relative bg-chat-input border border-chat-border hover:border-gray-600/60 focus-within:!border-brand-500 rounded-2xl shadow-lg transition-all duration-150 flex flex-col"
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question or research current events..."
          rows={1}
          disabled={isLoading && !isStreaming}
          className="w-full py-3.5 pl-4 pr-14 bg-transparent text-gray-100 placeholder-gray-500 text-[14.5px] resize-none focus:outline-none disabled:opacity-50 max-h-[200px] overflow-y-auto leading-relaxed"
        />

        {/* Action Button: Send or Stop */}
        <div className="absolute right-2.5 bottom-2.5">
          {isStreaming ? (
            <button
              type="button"
              onClick={onStopStreaming}
              className="w-8 h-8 rounded-xl bg-gray-700 hover:bg-red-600 text-white flex items-center justify-center transition-all duration-150 shadow-md group"
              title="Stop generating"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!canSend}
              className="w-8 h-8 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:bg-gray-800 disabled:text-gray-600 text-white flex items-center justify-center transition-all duration-150 disabled:cursor-not-allowed shadow-md shadow-brand-600/20 active:scale-95"
              title="Send message"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          )}
        </div>
      </form>

      {/* Footer disclaimer */}
      <div className="text-center mt-2 text-[11px] text-gray-500">
        AI responses may vary. Real-time web citations are retrieved dynamically when external verification is needed.
      </div>
    </div>
  );
}
