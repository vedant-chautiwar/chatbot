import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserPlus, AlertCircle, Loader2, Sparkles, CheckCircle } from 'lucide-react';

export function SignupView({ onSwitchToLogin }) {
  const { signUp, authError, setAuthError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    setAuthError(null);
    setSuccessMessage('');

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setValidationError('Please enter your email address.');
      return;
    }
    if (!password) {
      setValidationError('Please enter a password.');
      return;
    }
    if (password.length < 6) {
      setValidationError('Password must be at least 6 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match. Please verify your password confirmation.');
      return;
    }

    setLoading(true);
    try {
      const data = await signUp(cleanEmail, password);
      // Registration may require email confirmation or sign the user straight in
      if (data?.user && !data.session) {
        setSuccessMessage('Registration successful! Please check your email inbox to verify your account.');
      }
    } catch (err) {
      // Error is caught and surfaced via authError
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-chat-surface border border-chat-border rounded-2xl p-7 shadow-2xl backdrop-blur-sm">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-[#212121] border border-[#2e2e2e] text-white mb-3">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-2xl font-semibold text-white tracking-tight">Create your account</h2>
          <p className="text-xs text-[#a3a3a3] mt-1">Start intelligent conversations powered by agentic search</p>
        </div>

        {/* Success message */}
        {successMessage && (
          <div className="mb-5 p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-800/40 flex items-start gap-2.5 text-emerald-200 text-xs animate-fade-in">
            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">{successMessage}</div>
          </div>
        )}

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
            <label className="block text-xs font-medium text-[#a3a3a3] mb-1.5" htmlFor="signup-email">
              Email address
            </label>
            <input
              id="signup-email"
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
            <label className="block text-xs font-medium text-[#a3a3a3] mb-1.5" htmlFor="signup-password">
              Password
            </label>
            <input
              id="signup-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              disabled={loading}
              autoComplete="new-password"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#141414] border border-[#262626] text-[#ececec] placeholder-[#737373] text-sm focus:outline-none focus:border-[#404040] transition-colors disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#a3a3a3] mb-1.5" htmlFor="signup-confirm-password">
              Confirm password
            </label>
            <input
              id="signup-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter password"
              disabled={loading}
              autoComplete="new-password"
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
                <span>Creating account...</span>
              </>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Sign up</span>
              </>
            )}
          </button>
        </form>

        {/* Toggle to Login */}
        <div className="mt-6 text-center text-xs text-gray-400">
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-brand-500 hover:text-brand-400 font-medium transition-colors"
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}
