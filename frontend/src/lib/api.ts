import axios, { AxiosError } from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Single-flight refresh: with ROTATE_REFRESH_TOKENS on the backend, letting
// concurrent 401s each call /token/refresh/ would invalidate each other's
// tokens and force a logout. All callers await the same in-flight refresh.
let refreshPromise: Promise<string> | null = null;

function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return Promise.reject(new Error('No refresh token'));
    refreshPromise = axios
      .post(`${API_BASE}/auth/token/refresh/`, { refresh })
      .then((res) => {
        localStorage.setItem('access_token', res.data.access);
        if (res.data.refresh) {
          localStorage.setItem('refresh_token', res.data.refresh);
        }
        return res.data.access as string;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const access = await refreshAccessToken();
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

/** Extract a human-readable message from a DRF error response. */
export function getApiError(error: unknown, fallback = 'Something went wrong'): string {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<Record<string, unknown>>;
    if (err.response?.status === 403) {
      return "You don't have permission to do that.";
    }
    const data = err.response?.data;
    if (typeof data === 'string') return fallback;
    if (data) {
      if (typeof data.detail === 'string') return data.detail;
      const parts: string[] = [];
      for (const [field, value] of Object.entries(data)) {
        const messages = Array.isArray(value) ? value.join(' ') : String(value);
        parts.push(field === 'non_field_errors' ? messages : `${field}: ${messages}`);
      }
      if (parts.length) return parts.join('\n');
    }
    if (!err.response) return 'Network error — is the server running?';
  }
  return fallback;
}

export default api;
