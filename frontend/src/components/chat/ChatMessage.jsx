import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Copy, Check, Globe, Loader2, Sparkles } from 'lucide-react';
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
    let icon = <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400" />;

    if (streamStatus === 'searching') {
      label = 'Searching the web...';
      icon = <Globe className="w-3.5 h-3.5 animate-pulse text-cyan-400" />;
    } else if (streamStatus === 'generating') {
      label = 'Generating answer...';
      icon = <Sparkles className="w-3.5 h-3.5 animate-pulse text-violet-400" />;
    }

    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-chat-surface border border-chat-border text-xs text-gray-300 mb-3 animate-fade-in shadow-sm">
        {icon}
        <span className="font-medium text-[11px]">{label}</span>
      </div>
    );
  };

  return (
    <div
      className={`w-full py-4 px-4 sm:px-6 transition-colors ${
        isUser ? 'bg-transparent' : 'bg-chat-sidebar/40 border-y border-chat-border/30'
      }`}
    >
      <div className="max-w-3xl mx-auto flex gap-4 items-start">
        {/* Avatar */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-700/80 border border-gray-600 flex items-center justify-center text-gray-200 shadow-sm">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <Bot className="w-4 h-4 sm:w-4.5 sm:h-4.5" />
            </div>
          )}
        </div>

        {/* Content Body */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-gray-300">
              {isUser ? 'You' : 'CHAUTIBOT'}
            </span>

            {/* Copy message button */}
            {message.content && !isStreaming && (
              <button
                type="button"
                onClick={handleCopyMessage}
                className="opacity-0 group-hover:opacity-100 hover:opacity-100 p-1 rounded hover:bg-chat-surface text-gray-400 hover:text-gray-200 transition-all text-xs flex items-center gap-1"
                title="Copy message"
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
            )}
          </div>

          {/* Activity status badge while streaming */}
          {renderStatusBadge()}

          {/* Message content */}
          {isUser ? (
            <div className="text-gray-100 text-[15px] leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </div>
          ) : (
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
                          className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 transition-colors font-medium"
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
                <div className="text-gray-500 text-sm italic flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-brand-400 animate-ping" />
                  Generating response...
                </div>
              ) : null}

              {/* Streaming cursor indicator */}
              {isStreaming && message.content && (
                <span className="inline-block w-1.5 h-4 ml-0.5 bg-brand-400 animate-pulse align-middle" />
              )}
            </div>
          )}

          {/* Validated Web Search Sources */}
          {message.sources && message.sources.length > 0 && (
            <SourceCards sources={message.sources} />
          )}
        </div>
      </div>
    </div>
  );
}
