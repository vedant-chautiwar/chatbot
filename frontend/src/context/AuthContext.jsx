import React, { createContext, useContext, useState, useEffect } from 'react';
import { setAuthToken } from '../api/client';
import { loginApi, registerApi, fetchCurrentUserApi, logoutApi } from '../api/auth';

const AuthContext = createContext(null);

const STORAGE_TOKEN_KEY = 'agentic_chatbot_token';
const STORAGE_USER_KEY = 'agentic_chatbot_user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Sync token and user with API client and localStorage
  const updateSessionState = (authToken, authUser) => {
    if (authToken && authUser) {
      setToken(authToken);
      setUser(authUser);
      setAuthToken(authToken);
      localStorage.setItem(STORAGE_TOKEN_KEY, authToken);
      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(authUser));
    } else {
      setToken(null);
      setUser(null);
      setAuthToken(null);
      localStorage.removeItem(STORAGE_TOKEN_KEY);
      localStorage.removeItem(STORAGE_USER_KEY);
    }
  };

  useEffect(() => {
    let mounted = true;

    async function initializeAuth() {
      const savedToken = localStorage.getItem(STORAGE_TOKEN_KEY);
      const savedUserStr = localStorage.getItem(STORAGE_USER_KEY);

      if (!savedToken) {
        if (mounted) setLoading(false);
        return;
      }

      // Configure client with saved token
      setAuthToken(savedToken);
      if (savedUserStr) {
        try {
          setUser(JSON.parse(savedUserStr));
          setToken(savedToken);
        } catch {
          // ignore corrupted json
        }
      }

      try {
        // Validate saved token by fetching profile from FastAPI
        const profile = await fetchCurrentUserApi();
        if (mounted && profile) {
          const resolvedUser = {
            id: profile.id || profile.user_id,
            email: profile.email,
            name: profile.name || profile.email?.split('@')[0],
            role: profile.role || 'user',
          };
          updateSessionState(savedToken, resolvedUser);
        }
      } catch (err) {
        console.warn('Saved token expired or invalid:', err);
        if (mounted) {
          updateSessionState(null, null);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    initializeAuth();

    return () => {
      mounted = false;
    };
  }, []);

  // Login handler
  const login = async (email, password) => {
    setAuthError(null);
    try {
      const res = await loginApi(email, password);
      const authToken = res.access_token;
      const authUser = res.user;
      updateSessionState(authToken, authUser);
      return res;
    } catch (err) {
      const msg = err.message || 'Login failed. Please check your credentials.';
      setAuthError(msg);
      throw err;
    }
  };

  // Sign up handler
  const signUp = async (email, password, name = '') => {
    setAuthError(null);
    try {
      const res = await registerApi(email, password, name);
      const authToken = res.access_token;
      const authUser = res.user;
      updateSessionState(authToken, authUser);
      return res;
    } catch (err) {
      const msg = err.message || 'Registration failed. Please try again.';
      setAuthError(msg);
      throw err;
    }
  };

  // Demo / Offline login helper
  const loginWithDemoToken = (customToken = '', customEmail = 'user@example.com') => {
    const activeToken = customToken.trim() || 'demo_dev_token';
    const demoUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: customEmail,
      name: customEmail.split('@')[0],
      role: 'user',
    };
    updateSessionState(activeToken, demoUser);
  };

  // Logout handler
  const logout = async () => {
    try {
      await logoutApi();
    } catch (err) {
      console.warn('Logout API error:', err);
    } finally {
      updateSessionState(null, null);
    }
  };

  const value = {
    user,
    session: token ? { access_token: token, user } : null,
    token,
    loading,
    authError,
    setAuthError,
    login,
    signUp,
    logout,
    loginWithDemoToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
