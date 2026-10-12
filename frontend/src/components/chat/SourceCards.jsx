import React from 'react';
import { ExternalLink, Globe } from 'lucide-react';

export function SourceCards({ sources }) {
  if (!sources || !Array.isArray(sources) || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-5 pt-3 border-t border-[#212121]">
      <div className="flex items-center gap-2 mb-2.5">
        <div className="flex items-center gap-1.5 text-xs font-medium text-[#a3a3a3]">
          <Globe className="w-3.5 h-3.5 text-[#8e8e8e]" />
          <span>Sources</span>
        </div>
        <span className="px-1.5 py-0.2 rounded-full bg-[#1c1c1c] border border-[#2e2e2e] text-[#a3a3a3] text-[10px] font-medium">
          {sources.length}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {sources.map((source, index) => {
          const domain = source.domain || (source.url ? new URL(source.url).hostname.replace('www.', '') : 'source');
          const title = source.title || domain;

          return (
            <a
              key={source.url || index}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col justify-between p-2.5 rounded-xl bg-[#141414] hover:bg-[#1e1e1e] border border-[#262626] hover:border-[#383838] transition-colors duration-150 group text-left"
            >
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="w-4 h-4 rounded bg-[#212121] flex items-center justify-center text-[10px] text-[#a3a3a3] flex-shrink-0 font-medium">
                      {index + 1}
                    </span>
                    <span className="text-[11px] font-medium text-[#a3a3a3] truncate group-hover:text-white transition-colors">
                      {domain}
                    </span>
                  </div>
                  <ExternalLink className="w-3 h-3 text-[#737373] group-hover:text-white transition-colors flex-shrink-0" />
                </div>

                <h4 className="text-xs font-medium text-[#d4d4d8] line-clamp-2 leading-snug group-hover:text-white transition-colors">
                  {title}
                </h4>

                {source.snippet && (
                  <p className="mt-1 text-[11px] text-[#8e8e8e] line-clamp-2 leading-relaxed">
                    {source.snippet}
                  </p>
                )}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

