import React, { useRef, useEffect } from 'react';
import { ArrowUp, Square, Plus } from 'lucide-react';

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
    textarea.style.height = `${Math.max(nextHeight, 44)}px`;
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
    <div className="w-full max-w-[740px] mx-auto px-4 sm:px-6 pb-4 pt-1">
      <form
        onSubmit={handleFormSubmit}
        className="relative flex items-end gap-2 bg-[#2f2f2f] border border-transparent focus-within:border-[#444444] rounded-[28px] p-2 sm:p-2.5 shadow-lg transition-all duration-150"
      >
        {/* Attachment / Plus icon button */}
        <button
          type="button"
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-[#a3a3a3] hover:text-white hover:bg-[#3a3a3a] transition-colors mb-0.5 ml-0.5"
          title="Add attachment"
        >
          <Plus className="w-5 h-5" />
        </button>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
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
