import React, { useState } from 'react';
import { LoginView } from '../components/auth/LoginView';
import { SignupView } from '../components/auth/SignupView';
import { Bot, Globe, Zap, Shield } from 'lucide-react';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="min-h-screen w-full flex flex-col justify-between bg-black text-[#ececec] p-4 sm:p-8">
      {/* Top Navbar */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-2">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#1f1f1f] border border-[#2e2e2e] flex items-center justify-center text-white shadow-sm">
            <Bot className="w-4.5 h-4.5" />
          </div>
          <span className="font-semibold text-lg tracking-tight text-white">CHAUTIBOT</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl w-full mx-auto my-auto py-10 grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
        {/* Left column: Brand vision & capabilities */}
        <div className="hidden md:flex flex-col space-y-6 pr-6">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#171717] border border-[#2e2e2e] text-[#a3a3a3] text-xs font-medium">
              <Zap className="w-3.5 h-3.5" />
              <span>Groq LLM + Real-Time Tavily Search</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white leading-tight">
              Intelligent answers with real-time web grounding.
            </h1>
            <p className="text-sm sm:text-base text-[#a3a3a3] leading-relaxed">
              Experience an agentic conversational assistant that dynamically determines when to retrieve verified external evidence and cite web sources.
            </p>
          </div>

          <div className="space-y-3.5 pt-2">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-[#141414] border border-[#262626] text-[#a3a3a3] mt-0.5">
                <Globe className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#f5f5f5]">Autonomous Web Retrieval</h3>
                <p className="text-xs text-[#8e8e8e]">Pulls live web evidence only when needed, with real source citations.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-[#141414] border border-[#262626] text-[#a3a3a3] mt-0.5">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#f5f5f5]">High-Velocity Groq Inference</h3>
                <p className="text-xs text-[#8e8e8e]">Stream responses progressively with low-latency token delivery.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-[#141414] border border-[#262626] text-[#a3a3a3] mt-0.5">
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#f5f5f5]">Isolated & Persisted Chats</h3>
                <p className="text-xs text-[#8e8e8e]">Protected user accounts and conversations stored securely in MongoDB.</p>
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
