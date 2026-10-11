import React, { useState } from 'react';
import { LoginView } from '../components/auth/LoginView';
import { SignupView } from '../components/auth/SignupView';
import { Bot, Globe, Zap, Shield } from 'lucide-react';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="min-h-screen w-full flex flex-col justify-between bg-chat-bg text-gray-100 p-4 sm:p-8">
      {/* Top Navbar */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-2">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <span className="font-semibold text-lg tracking-tight text-white">CHAUTIBOT</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl w-full mx-auto my-auto py-10 grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
        {/* Left column: Brand vision & capabilities */}
        <div className="hidden md:flex flex-col space-y-6 pr-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-medium">
              <Zap className="w-3.5 h-3.5" />
              <span>Groq LLM + Real-Time Tavily Search</span>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
              Intelligent answers with real-time web grounding.
            </h1>
            <p className="text-base text-gray-400 leading-relaxed">
              Experience an agentic conversational assistant that dynamically determines when to retrieve verified external evidence and cite web sources.
            </p>
          </div>

          <div className="space-y-3.5 pt-2">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-chat-surface border border-chat-border text-brand-400 mt-0.5">
                <Globe className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-200">Autonomous Web Retrieval</h3>
                <p className="text-xs text-gray-400">Pulls live web evidence only when needed, with real source citations.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-chat-surface border border-chat-border text-cyan-400 mt-0.5">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-200">High-Velocity Groq Inference</h3>
                <p className="text-xs text-gray-400">Stream responses progressively with low-latency token delivery.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-chat-surface border border-chat-border text-emerald-400 mt-0.5">
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-200">Isolated & Persisted Chats</h3>
                <p className="text-xs text-gray-400">Protected user accounts and conversations stored securely in MongoDB.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right column: Form */}
        <div className="flex justify-center">
          {isLogin ? (
            <LoginView onSwitchToSignup={() => setIsLogin(false)} />
          ) : (
            <SignupView onSwitchToLogin={() => setIsLogin(true)} />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-6xl w-full mx-auto text-center py-4 text-xs text-gray-500">
        CHAUTIBOT with Web Search &bull; Fast, grounded, and secure.
      </footer>
    </div>
  );
}
