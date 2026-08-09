'use client';

import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import api from './api';
import { User } from '@/types';

/** Users are signed out after this much inactivity (matches the backend's
 * 5-minute access-token lifetime; the refresh token dies at 10 minutes). */
const INACTIVITY_LIMIT_MS = 5 * 60 * 1000;
const ACTIVITY_KEY = 'last_activity';
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'click'] as const;

function lastActivity(): number {
  const raw = localStorage.getItem(ACTIVITY_KEY);
  const ts = raw ? parseInt(raw, 10) : NaN;
  return Number.isFinite(ts) ? ts : 0;
}

function isIdleTooLong(): boolean {
  const ts = lastActivity();
  return ts > 0 && Date.now() - ts > INACTIVITY_LIMIT_MS;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithTokens: (access: string, refresh: string) => Promise<void>;
  logout: (expired?: boolean) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const userRef = useRef<User | null>(null);
  userRef.current = user;

  const clearSession = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem(ACTIVITY_KEY);
    setUser(null);
  };

  const logout = (expired = false) => {
    clearSession();
    if (expired) {
      // Survives the racing dashboard-layout redirect that strips query params.
      sessionStorage.setItem('session_expired', '1');
    }
    router.push('/login');
  };

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      // A session left idle past the limit is dead even if the tab was
      // closed while the timer wasn't running.
      if (isIdleTooLong()) {
        clearSession();
        sessionStorage.setItem('session_expired', '1');
        setLoading(false);
        router.push('/login');
        return;
      }
      const res = await api.get('/auth/me/');
      setUser(res.data);
      localStorage.setItem(ACTIVITY_KEY, String(Date.now()));
    } catch {
      clearSession();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  // Inactivity watcher: any user interaction (in any tab — localStorage is
  // shared) refreshes the activity timestamp; a periodic check signs the
  // user out once the limit passes.
  useEffect(() => {
    if (!user) return;

    let lastWrite = 0;
    const recordActivity = () => {
      const now = Date.now();
      if (now - lastWrite > 10_000) {
        lastWrite = now;
        localStorage.setItem(ACTIVITY_KEY, String(now));
      }
    };
    recordActivity();

    const checkIdle = () => {
      if (userRef.current && isIdleTooLong()) {
        logout(true);
      }
    };

    ACTIVITY_EVENTS.forEach((evt) => window.addEventListener(evt, recordActivity, { passive: true }));
    const interval = setInterval(checkIdle, 15_000);
    document.addEventListener('visibilitychange', checkIdle);

    return () => {
      ACTIVITY_EVENTS.forEach((evt) => window.removeEventListener(evt, recordActivity));
      clearInterval(interval);
      document.removeEventListener('visibilitychange', checkIdle);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loginWithTokens = async (access: string, refresh: string) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem(ACTIVITY_KEY, String(Date.now()));
    await refreshUser();
    router.push('/dashboard');
  };

  const login = async (email: string, password: string) => {
    const res = await api.post('/auth/login/', { email, password });
    await loginWithTokens(res.data.access, res.data.refresh);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithTokens, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
