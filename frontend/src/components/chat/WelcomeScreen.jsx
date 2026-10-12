import React from 'react';
import { Sparkles, Compass, Lightbulb, Code2 } from 'lucide-react';

export function WelcomeScreen({ onSelectPrompt }) {
  const suggestions = [
    {
      title: 'Explain a complex concept simply',
      description: 'How does transformer self-attention work?',
      icon: Lightbulb,
      prompt: 'Explain how transformer self-attention works in simple, intuitive terms with a clear analogy.',
    },
    {
      title: 'Explore the latest AI developments',
      description: 'What are the latest breakthrough releases?',
      icon: Compass,
      prompt: 'What are the latest breakthrough releases and major updates in AI?',
    },
    {
      title: 'Compare two technologies',
      description: 'FastAPI vs Express.js for modern APIs',
      icon: Sparkles,
      prompt: 'Compare FastAPI vs Express.js for modern APIs. What are the key architectural differences and trade-offs?',
    },
    {
      title: 'Help debug a piece of code',
      description: 'Find issues in async Python or React hooks',
      icon: Code2,
      prompt: 'Help debug a piece of code: what are common issues and subtle bugs in async Python or React hooks?',
    },
  ];

  return (
    <div className="h-full flex flex-col items-center justify-center px-4 py-12 select-none animate-fade-in">
      <div className="w-full max-w-[680px] flex flex-col items-center text-center">
        {/* Brand icon */}
        <div className="w-11 h-11 rounded-full bg-[#1c1c1c] border border-[#2e2e2e] flex items-center justify-center mb-5 shadow-sm">
          <Sparkles className="w-5 h-5 text-white" />
        </div>

        <h1 className="text-[28px] sm:text-[32px] font-semibold tracking-tight text-white mb-2.5 leading-tight">
          Where should we start?
        </h1>

        <p className="text-[14px] text-[#a3a3a3] max-w-[440px] mb-9 leading-relaxed">
          Ask anything — I can answer from foundational knowledge or search the web in real-time when needed.
        </p>

        {/* Suggested prompt cards: 2-column grid */}
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
          {suggestions.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={index}
                type="button"
                onClick={() => onSelectPrompt(item.prompt)}
                className="group p-4 rounded-2xl bg-[#141414] hover:bg-[#1a1a1a] border border-[#262626] hover:border-[#333333] transition-all duration-150 flex items-start gap-3 text-left active:scale-[0.99]"
              >
                <div className="mt-0.5 p-1.5 rounded-lg bg-[#1f1f1f] border border-[#2a2a2a] text-[#a3a3a3] group-hover:text-white transition-colors flex-shrink-0">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-medium text-[#ececec] group-hover:text-white leading-snug">
                    {item.title}
                  </p>
                  <p className="text-[12px] text-[#737373] mt-0.5 line-clamp-2 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
