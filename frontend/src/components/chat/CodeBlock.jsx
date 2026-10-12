import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

// Custom dark theme closely matching ChatGPT's code style
const chautibotCodeTheme = {
  'code[class*="language-"]': {
    color: '#f8f8f2',
    background: 'none',
    fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Monaco, 'Courier New', monospace",
    fontSize: '0.855rem',
    textAlign: 'left',
    whiteSpace: 'pre',
    wordSpacing: 'normal',
    wordBreak: 'normal',
    wordWrap: 'normal',
    lineHeight: '1.6',
    tabSize: 4,
    hyphens: 'none',
  },
  'pre[class*="language-"]': {
    color: '#f8f8f2',
    background: '#0d0d0d',
    fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Monaco, 'Courier New', monospace",
    fontSize: '0.855rem',
    textAlign: 'left',
    whiteSpace: 'pre',
    wordSpacing: 'normal',
    wordBreak: 'normal',
    wordWrap: 'normal',
    lineHeight: '1.6',
    tabSize: 4,
    hyphens: 'none',
    padding: '1.1rem 1.25rem',
    margin: '0',
    overflow: 'auto',
  },
  comment: { color: '#636363', fontStyle: 'italic' },
  prolog: { color: '#636363' },
  doctype: { color: '#636363' },
  cdata: { color: '#636363' },
  punctuation: { color: '#c0c0c0' },
  namespace: { opacity: '0.7' },
  property: { color: '#f38ba8' },
  tag: { color: '#f38ba8' },
  boolean: { color: '#fab387' },
  number: { color: '#fab387' },
  constant: { color: '#fab387' },
  symbol: { color: '#f9e2af' },
  deleted: { color: '#f38ba8' },
  selector: { color: '#a6e3a1' },
  'attr-name': { color: '#a6e3a1' },
  string: { color: '#a6e3a1' },
  char: { color: '#a6e3a1' },
  builtin: { color: '#89dceb' },
  inserted: { color: '#a6e3a1' },
  operator: { color: '#89dceb' },
  entity: { color: '#f9e2af', cursor: 'help' },
  url: { color: '#89b4fa' },
  variable: { color: '#89b4fa' },
  atrule: { color: '#cba6f7' },
  'attr-value': { color: '#a6e3a1' },
  function: { color: '#89b4fa' },
  'class-name': { color: '#f9e2af' },
  keyword: { color: '#cba6f7' },
  regex: { color: '#f5c2e7' },
  important: { color: '#fab387', fontWeight: 'bold' },
  bold: { fontWeight: 'bold' },
  italic: { fontStyle: 'italic' },
};

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

  const displayLang = language || 'text';

  return (
    <div className="relative my-4 rounded-xl overflow-hidden border border-[#242424] bg-[#0d0d0d] shadow-md group">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#161616] border-b border-[#242424] text-xs text-[#a3a3a3]">
        <span className="font-mono lowercase text-[#8a8a8a] font-medium tracking-wide">{displayLang}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-0.5 rounded text-xs text-[#8a8a8a] hover:text-white transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[11px] text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="text-[11px]">Copy code</span>
            </>
          )}
        </button>
      </div>

      {/* Syntax-highlighted Code Content */}
      <SyntaxHighlighter
        language={displayLang}
        style={chautibotCodeTheme}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          background: '#0d0d0d',
        }}
        wrapLongLines={false}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}
