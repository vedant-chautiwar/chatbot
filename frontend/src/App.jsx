import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AuthPage } from './pages/AuthPage';
import { ChatPage } from './pages/ChatPage';
import { Loader2 } from 'lucide-react';

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-chat-bg">
        <div className="flex flex-col items-center gap-3 text-gray-400">
          <Loader2 className="w-7 h-7 animate-spin text-brand-400" />
          <span className="text-sm font-medium">Starting CHAUTIBOT...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <ChatPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
