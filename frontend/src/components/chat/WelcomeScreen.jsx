import React from 'react';
import { Sparkles, Globe, Cpu, Code2, ArrowUpRight } from 'lucide-react';

export function WelcomeScreen({ onSelectPrompt }) {
  const suggestions = [
    {
      title: 'Explain a complex concept simply',
      description: 'e.g., How does transformer self-attention work?',
      icon: Sparkles,
      prompt: 'Explain how transformer self-attention works in simple, intuitive terms with a clear analogy.',
    },
    {
      title: 'Explore the latest AI developments',
      description: 'e.g., What are the latest breakthrough releases this week?',
      icon: Globe,
      prompt: 'What are the most significant recent developments and breakthrough models announced in AI lately?',
    },
    {
      title: 'Compare two technologies',
      description: 'e.g., FastAPI vs Express.js for modern APIs',
      icon: Cpu,
      prompt: 'Compare FastAPI and Express.js for building scalable modern APIs. What are their core trade-offs?',
    },
    {
      title: 'Help debug a piece of code',
      description: 'e.g., Find issues in async Python or React hooks',
      icon: Code2,
      prompt: 'Can you help me understand common pitfalls and memory leaks with React useEffect and how to avoid them?',
    },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 max-w-2xl mx-auto my-auto text-center animate-fade-in">
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white mb-5 shadow-xl shadow-brand-500/10">
        <Sparkles className="w-6 h-6" />
      </div>

      <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-2.5">
        Where should we start?
      </h1>

      <p className="text-sm sm:text-base text-gray-400 max-w-lg mb-8 leading-relaxed">
        Ask anything — I can answer directly from foundational knowledge or research real-time information with autonomous web search when needed.
      </p>

      <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
        {suggestions.map((item, index) => {
          const Icon = item.icon;
          return (
            <button
              key={index}
              type="button"
              onClick={() => onSelectPrompt(item.prompt)}
              className="group p-4 rounded-xl bg-chat-surface hover:bg-chat-surfaceHover border border-chat-border hover:border-brand-500/40 text-left transition-all duration-150 flex flex-col justify-between shadow-sm hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="p-2 rounded-lg bg-chat-elevated text-brand-400 group-hover:text-brand-300 transition-colors">
                  <Icon className="w-4 h-4" />
                </div>
                <ArrowUpRight className="w-4 h-4 text-gray-500 group-hover:text-brand-400 transition-colors opacity-0 group-hover:opacity-100" />
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">
                  {item.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
