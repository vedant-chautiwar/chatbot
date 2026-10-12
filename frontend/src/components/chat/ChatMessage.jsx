import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, Globe, Loader2, Sparkles } from 'lucide-react';
import { CodeBlock } from './CodeBlock';
import { SourceCards } from './SourceCards';

export function ChatMessage({ message, isStreaming = false, streamStatus = null }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopyMessage = async () => {
    try {
      await navigator.clipboard.writeText(message.content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  // Status message for streaming
  const renderStatusBadge = () => {
    if (!isStreaming || !streamStatus) return null;

    let label = 'Thinking...';
    let icon = <Loader2 className="w-3.5 h-3.5 animate-spin text-[#a3a3a3]" />;

    if (streamStatus === 'searching') {
      label = 'Searching the web with Tavily...';
      icon = <Globe className="w-3.5 h-3.5 animate-pulse text-[#60a5fa]" />;
    } else if (streamStatus === 'generating') {
      label = 'Generating response...';
      icon = <Sparkles className="w-3.5 h-3.5 animate-pulse text-[#a3a3a3]" />;
    }

    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#171717] border border-[#262626] text-xs text-[#a3a3a3] mb-3 animate-fade-in">
        {icon}
        <span className="font-medium text-[12px]">{label}</span>
      </div>
    );
  };

  // USER MESSAGE: Compact right-aligned bubble container
  if (isUser) {
    return (
      <div className="w-full max-w-[740px] mx-auto px-4 sm:px-6 my-3 flex justify-end">
        <div className="max-w-[85%] sm:max-w-[70%] bg-[#2f2f2f] text-[#ececec] px-[18px] py-3 rounded-[20px] text-[15px] leading-relaxed break-words whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  // ASSISTANT MESSAGE: Clean unboxed text directly on black canvas
  return (
    <div className="w-full max-w-[740px] mx-auto px-4 sm:px-6 my-4 transition-colors">
      <div className="w-full">
        {/* Activity status badge while streaming */}
        {renderStatusBadge()}

        {/* Message body */}
        <div className="prose-chat break-words">
          {message.content ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const codeContent = String(children).replace(/\n$/, '');
                  if (!inline && match) {
                    return (
                      <CodeBlock
                        language={match[1]}
                        value={codeContent}
                      />
                    );
                  }
                  if (!inline && !match && codeContent.includes('\n')) {
                    return (
                      <CodeBlock
                        language=""
                        value={codeContent}
                      />
                    );
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                a({ href, children }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#60a5fa] hover:text-[#93c5fd] underline underline-offset-2 transition-colors font-medium"
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : isStreaming ? (
            <div className="text-[#737373] text-sm italic flex items-center gap-2 py-1">
              <span className="inline-block w-2 h-2 rounded-full bg-[#a3a3a3] animate-ping" />
              Generating response...
            </div>
          ) : null}

          {/* Streaming cursor indicator */}
          {isStreaming && message.content && (
            <span className="inline-block w-1.5 h-4 ml-0.5 bg-[#ececec] animate-pulse align-middle" />
          )}
        </div>

        {/* Validated Web Search Sources */}
        {message.sources && message.sources.length > 0 && (
          <SourceCards sources={message.sources} />
        )}

        {/* Action icons below assistant message */}
        {message.content && !isStreaming && (
          <div className="flex items-center gap-1 mt-3 -ml-1 text-[#8e8e8e]">
            <button
              type="button"
              onClick={handleCopyMessage}
              className="p-1.5 rounded-lg hover:bg-[#1c1c1c] hover:text-[#ececec] transition-colors text-xs flex items-center gap-1.5"
              title="Copy response"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[11px] text-emerald-400">Copied</span>
                </>
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

