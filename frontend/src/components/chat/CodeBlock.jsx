import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

export function CodeBlock({ language, value }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const displayLang = language || 'code';

  return (
    <div className="relative my-4 rounded-xl overflow-hidden border border-chat-border bg-[#141720] shadow-md group">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#1a1e29] border-b border-chat-border text-xs text-gray-400">
        <span className="font-mono lowercase text-gray-300 font-medium">{displayLang}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-chat-surface text-gray-300 hover:text-white transition-colors"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="text-xs">Copy code</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content */}
      <div className="overflow-x-auto p-4 text-[13.5px] font-mono leading-relaxed text-gray-100">
        <pre className="!bg-transparent !p-0 !m-0">
          <code>{value}</code>
        </pre>
      </div>
    </div>
  );
}
