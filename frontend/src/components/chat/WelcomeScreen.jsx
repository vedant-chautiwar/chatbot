import React from 'react';
import { Sparkles, Compass, FileText, Code2, Bug } from 'lucide-react';

export function WelcomeScreen({ onSelectPrompt }) {
  const suggestions = [
    {
      title: 'Analyze or summarize a document',
      description: 'Upload a PDF, TXT, or Markdown file to extract key points or ask questions.',
      icon: FileText,
      prompt: 'Can you summarize the main findings and key points from my attached document?',
    },
    {
      title: 'Explain a code snippet or algorithm',
      description: 'Break down execution flow, classes, or unfamiliar libraries simply.',
      icon: Code2,
      prompt: 'Explain how this code works step-by-step, including its time and space complexity:\n\n```python\ndef binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n```',
    },
    {
      title: 'Debug and improve code',
      description: 'Identify syntax/logical bugs, edge cases, and performance bottlenecks.',
      icon: Bug,
      prompt: 'Find the logical bug and edge case flaws in this function and suggest an optimized fix:\n\n```python\ndef get_average_scores(student_records):\n    averages = {}\n    for student, scores in student_records.items():\n        averages[student] = sum(scores) / len(scores)\n    return averages\n```',
    },
    {
      title: 'Explore the latest AI developments',
      description: 'Search live news, breakthrough model releases, and benchmarks.',
      icon: Compass,
      prompt: 'What are the latest breakthrough releases and major updates in AI?',
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

        <p className="text-[14px] text-[#a3a3a3] max-w-[480px] mb-9 leading-relaxed">
          Ask anything, paste code, or attach documents — powered by live web search, RAG document analysis, and an expert code assistant.
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
