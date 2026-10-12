import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogIn, AlertCircle, Loader2, Sparkles, Key } from 'lucide-react';

export function LoginView({ onSwitchToSignup }) {
  const { login, loginWithDemoToken, authError, setAuthError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    setAuthError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setValidationError('Please enter your email address.');
      return;
    }
    if (!password) {
      setValidationError('Please enter your password.');
      return;
    }

    setLoading(true);
    try {
      await login(cleanEmail, password);
    } catch (err) {
      // Error is set in AuthContext and shown in alert banner
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = () => {
    loginWithDemoToken('', 'demo_user@example.com');
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-chat-surface border border-chat-border rounded-2xl p-7 shadow-2xl backdrop-blur-sm">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-[#212121] border border-[#2e2e2e] text-white mb-3">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-2xl font-semibold text-white tracking-tight">Welcome back</h2>
          <p className="text-xs text-[#a3a3a3] mt-1">Sign in to your CHAUTIBOT account</p>
        </div>

        {/* Validation or Auth Error */}
        {(validationError || authError) && (
          <div className="mb-5 p-3 rounded-xl bg-red-950/30 border border-red-800/40 flex items-start gap-2.5 text-red-200 text-xs animate-fade-in">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">{validationError || authError}</div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#a3a3a3] mb-1.5" htmlFor="login-email">
              Email address
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              disabled={loading}
              autoComplete="email"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#141414] border border-[#262626] text-[#ececec] placeholder-[#737373] text-sm focus:outline-none focus:border-[#404040] transition-colors disabled:opacity-50"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-medium text-[#a3a3a3] mb-1.5" htmlFor="login-password">
                Password
              </label>
            </div>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
              autoComplete="current-password"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#141414] border border-[#262626] text-[#ececec] placeholder-[#737373] text-sm focus:outline-none focus:border-[#404040] transition-colors disabled:opacity-50"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 rounded-xl bg-white hover:bg-[#e5e5e5] text-black font-medium text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50 shadow-sm active:scale-[0.99]"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-black" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign in</span>
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Access */}
        <div className="mt-4 pt-4 border-t border-[#262626]">
          <button
            type="button"
            onClick={handleQuickDemo}
            className="w-full py-2 px-3 rounded-xl bg-[#141414] hover:bg-[#1f1f1f] border border-[#262626] text-xs text-[#a3a3a3] hover:text-white flex items-center justify-center gap-1.5 transition-colors"
          >
            <Key className="w-3.5 h-3.5 text-[#a3a3a3]" />
            <span>Instant Demo Sign In (Explore UI)</span>
          </button>
        </div>

        {/* Toggle to Signup */}
        <div className="mt-5 text-center text-xs text-gray-400">
          Don't have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToSignup}
            className="text-brand-500 hover:text-brand-400 font-medium transition-colors"
          >
            Create an account
          </button>
        </div>
      </div>
    </div>
  );
}
