'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { apiFetch, requireAuth } from '@/lib/api';
import { useRouter } from 'next/navigation';

type Product = {
  id: number;
  prom_uid: string;
  name: string;
  price: number;
  qty: number;
  availability: string;
  group_name?: string;
};

export default function ProductsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Product[]>([]);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch(`/products?q=${encodeURIComponent(search)}&page=${page}&per_page=${perPage}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!requireAuth(router.push)) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const save = async (p: Product) => {
    setError('');
    try {
      const updated = await apiFetch(`/products/${p.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ price: p.price, qty: p.qty, availability: p.availability })
      });
      setItems((prev) => prev.map((item) => (item.id === p.id ? updated : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    }
  };

  const pages = Math.max(1, Math.ceil(total / perPage));

  return (
    <main className="container">
      <div className="card">
        <h1>Товари</h1>
        <nav>
          <Link href="/products">Товари</Link>
          <Link href="/inventory">Склад</Link>
          <Link href="/orders">Замовлення</Link>
          <Link href="/login">Логін</Link>
        </nav>

        <div className="row" style={{ marginBottom: 12 }}>
          <button onClick={async () => {
            setError("");
            try {
              await apiFetch("/prom/sync/products", { method: "POST" });
              await load();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Sync failed");
            }
          }}>Синхронізувати з Prom</button>
          <button className="secondary" onClick={() => load()}>Оновити</button>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Пошук по назві або UID"
            style={{ minWidth: 260 }}
          />
          <button onClick={() => { setPage(1); load(); }}>Шукати</button>
        </div>

        {error && <p className="error">{error}</p>}
        {loading ? (
          <p>Завантаження...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>UID</th>
                <th>Назва</th>
                <th>Група</th>
                <th>Ціна</th>
                <th>К-сть</th>
                <th>Наявність</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.prom_uid}</td>
                  <td>{p.name}</td>
                  <td>{p.group_name || '-'}</td>
                  <td>
                    <input
                      type="number"
                      min={0}
                      value={p.price}
                      onChange={(e) => setItems((prev) => prev.map((x) => (x.id === p.id ? { ...x, price: Number(e.target.value) } : x)))}
                      style={{ width: 90 }}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      min={0}
                      value={p.qty}
                      onChange={(e) => setItems((prev) => prev.map((x) => (x.id === p.id ? { ...x, qty: Number(e.target.value) } : x)))}
                      style={{ width: 80 }}
                    />
                  </td>
                  <td>
                    <select
                      value={p.availability}
                      onChange={(e) =>
                        setItems((prev) => prev.map((x) => (x.id === p.id ? { ...x, availability: e.target.value } : x)))
                      }
                    >
                      <option value="available">available</option>
                      <option value="unavailable">unavailable</option>
                      <option value="preorder">preorder</option>
                    </select>
                  </td>
                  <td>
                    <button onClick={() => save(p)}>Зберегти</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="row" style={{ marginTop: 16, alignItems: 'center' }}>
          <button className="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Назад
          </button>
          <span>
            Сторінка {page} / {pages}
          </span>
          <button className="secondary" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
            Вперед
          </button>
        </div>
      </div>
    </main>
  );
}
