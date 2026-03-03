'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_URL } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Login failed');
      }
      localStorage.setItem('token', data.access_token);
      router.push('/products');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: 420, margin: '30px auto' }}>
        <h1>Admin Login</h1>
        <form onSubmit={onSubmit}>
          <div className="row" style={{ flexDirection: 'column' }}>
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="ADMIN_USER" required />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="ADMIN_PASS"
              required
            />
            <button disabled={loading}>{loading ? 'Вхід...' : 'Увійти'}</button>
          </div>
          {error && <p className="error">{error}</p>}
        </form>
      </div>
    </main>
  );
}
