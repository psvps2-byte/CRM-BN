'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { apiFetch, requireAuth } from '@/lib/api';
import { useRouter } from 'next/navigation';

type OrderItem = {
  id: number;
  name: string;
  quantity: number;
  price: number;
};

type Order = {
  id: number;
  prom_uid: string;
  status: string;
  total_price: number;
  currency: string;
  customer_name?: string;
  customer_phone?: string;
  created_at: string;
  items: OrderItem[];
};

export default function OrdersPage() {
  const router = useRouter();
  const [items, setItems] = useState<Order[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch('/orders?page=1&per_page=50');
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  };

  const syncOrders = async () => {
    setError('');
    try {
      await apiFetch('/prom/sync/orders', { method: 'POST' });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
    }
  };

  useEffect(() => {
    if (!requireAuth(router.push)) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="container">
      <div className="card">
        <h1>Замовлення</h1>
        <nav>
          <Link href="/products">Товари</Link>
          <Link href="/inventory">Склад</Link>
          <Link href="/orders">Замовлення</Link>
          <Link href="/login">Логін</Link>
        </nav>

        <div className="row" style={{ marginBottom: 16 }}>
          <button onClick={syncOrders}>Синхронізувати замовлення з Prom</button>
          <button className="secondary" onClick={load}>Оновити список</button>
        </div>

        {error && <p className="error">{error}</p>}
        {loading ? (
          <p>Завантаження...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Prom UID</th>
                <th>Клієнт</th>
                <th>Статус</th>
                <th>Сума</th>
                <th>Позиції</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {items.map((order) => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{order.prom_uid}</td>
                  <td>
                    {order.customer_name || '-'}
                    {order.customer_phone ? ` (${order.customer_phone})` : ''}
                  </td>
                  <td>{order.status}</td>
                  <td>
                    {order.total_price} {order.currency}
                  </td>
                  <td>{order.items.map((i) => `${i.name} x${i.quantity}`).join(', ') || '-'}</td>
                  <td>{new Date(order.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
