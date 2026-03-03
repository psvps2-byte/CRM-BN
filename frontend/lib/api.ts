const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
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
