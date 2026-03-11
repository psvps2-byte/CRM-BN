const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  'https://backend-production-c878.up.railway.app';

const TOKEN_KEY = 'token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(options.headers ?? {});
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers
  });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      message = data.detail || message;
    } catch {
      // no-op
    }
    if (res.status === 401) {
      clearToken();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    throw new Error(message);
  }

  return res.json();
}

export function requireAuth(redirect: (path: string) => void) {
  if (!getToken()) {
    redirect('/login');
    return false;
  }
  return true;
}

export { API_URL };
