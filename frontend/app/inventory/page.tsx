'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { apiFetch, requireAuth } from '@/lib/api';
import { useRouter } from 'next/navigation';

type Movement = {
  id: number;
  product_id: number;
  product_name: string;
  movement_type: 'IN' | 'OUT' | 'ADJUST';
  quantity: number;
  note?: string;
  created_at: string;
};

export default function InventoryPage() {
  const router = useRouter();
  const [movements, setMovements] = useState<Movement[]>([]);
  const [productId, setProductId] = useState('');
  const [movementType, setMovementType] = useState<'IN' | 'OUT' | 'ADJUST'>('IN');
  const [quantity, setQuantity] = useState('1');
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const loadMovements = async () => {
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch('/inventory/movements?limit=100');
      setMovements(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!requireAuth(router.push)) return;
    loadMovements();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await apiFetch('/inventory/movements', {
        method: 'POST',
        body: JSON.stringify({
          product_id: Number(productId),
          movement_type: movementType,
          quantity: Number(quantity),
          note: note || null
        })
      });
      setQuantity('1');
      setNote('');
      await loadMovements();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  };

  return (
    <main className="container">
      <div className="card">
        <h1>Склад</h1>
        <nav>
          <Link href="/products">Товари</Link>
          <Link href="/inventory">Склад</Link>
          <Link href="/orders">Замовлення</Link>
          <Link href="/login">Логін</Link>
        </nav>

        <form className="card" onSubmit={submit} style={{ marginBottom: 16 }}>
          <h3>Новий рух</h3>
          <div className="row">
            <input
              type="number"
              min={1}
              placeholder="Product ID"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              required
            />
            <select value={movementType} onChange={(e) => setMovementType(e.target.value as 'IN' | 'OUT' | 'ADJUST')}>
              <option value="IN">IN</option>
              <option value="OUT">OUT</option>
              <option value="ADJUST">ADJUST</option>
            </select>
            <input
              type="number"
              min={1}
              placeholder="Кількість"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
            />
            <input placeholder="Нотатка" value={note} onChange={(e) => setNote(e.target.value)} />
            <button type="submit">Створити</button>
          </div>
        </form>

        {error && <p className="error">{error}</p>}
        {loading ? (
          <p>Завантаження...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Товар</th>
                <th>Тип</th>
                <th>К-сть</th>
                <th>Нотатка</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>
                    {m.product_name} (#{m.product_id})
                  </td>
                  <td>{m.movement_type}</td>
                  <td>{m.quantity}</td>
                  <td>{m.note || '-'}</td>
                  <td>{new Date(m.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
