import React from 'react';
import { ExternalLink, Globe, Calendar } from 'lucide-react';

export function SourceCards({ sources }) {
  if (!sources || !Array.isArray(sources) || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 pt-3.5 border-t border-chat-border/60">
      <div className="flex items-center gap-2 mb-2.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-300 uppercase tracking-wider">
          <Globe className="w-3.5 h-3.5 text-cyan-400" />
          <span>Web Sources</span>
        </div>
        <span className="px-1.5 py-0.2 rounded-full bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 text-[11px] font-medium">
          {sources.length}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {sources.map((source, index) => {
          const domain = source.domain || (source.url ? new URL(source.url).hostname : 'source');
          const title = source.title || domain;

          return (
            <a
              key={source.url || index}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col justify-between p-3 rounded-xl bg-chat-surface hover:bg-chat-surfaceHover border border-chat-border hover:border-gray-600/60 transition-all duration-150 group text-left"
            >
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="w-4 h-4 rounded bg-gray-800 flex items-center justify-center text-[10px] text-gray-400 flex-shrink-0 font-medium">
                      {index + 1}
                    </span>
                    <span className="text-[11px] font-medium text-cyan-400/90 truncate">
                      {domain}
                    </span>
                  </div>
                  <ExternalLink className="w-3 h-3 text-gray-500 group-hover:text-cyan-400 transition-colors flex-shrink-0" />
                </div>

                <h4 className="text-xs font-medium text-gray-200 line-clamp-2 leading-snug group-hover:text-white transition-colors">
                  {title}
                </h4>

                {source.snippet && (
                  <p className="mt-1 text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                    {source.snippet}
                  </p>
                )}
              </div>

              {source.published_date && (
                <div className="mt-2 pt-1.5 flex items-center gap-1 text-[10px] text-gray-500 border-t border-chat-border/40">
                  <Calendar className="w-3 h-3" />
                  <span>{source.published_date}</span>
                </div>
              )}
            </a>
          );
        })}
      </div>
    </div>
  );
}
