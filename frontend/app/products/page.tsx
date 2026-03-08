'use client';

import CrmSidebar from '@/components/crm-sidebar';
import { apiFetch, requireAuth } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

type Product = {
  id: number;
  prom_uid: string;
  name: string;
  price: number;
  qty: number;
  availability: string;
  group_name?: string;
  slug?: string | null;
  description?: string | null;
  attributes?: Record<string, string> | null;
  image_urls?: string[] | null;
};

function formatAttributes(attributes?: Record<string, string> | null) {
  if (!attributes) return '';
  return Object.entries(attributes)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');
}

function parseAttributes(input: string) {
  const rows = input
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  if (!rows.length) return null;

  const result: Record<string, string> = {};
  for (const row of rows) {
    const splitIndex = row.indexOf(':');
    if (splitIndex <= 0) continue;
    const key = row.slice(0, splitIndex).trim();
    const value = row.slice(splitIndex + 1).trim();
    if (key) result[key] = value;
  }
  return Object.keys(result).length ? result : null;
}

function formatImageUrls(urls?: string[] | null) {
  if (!urls?.length) return '';
  return urls.join('\n');
}

function parseImageUrls(input: string) {
  const rows = input
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
  return rows.length ? rows : null;
}

export default function ProductsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Product[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [search, setSearch] = useState('');
  const [attributesDraft, setAttributesDraft] = useState('');
  const [imagesDraft, setImagesDraft] = useState('');
  const [page, setPage] = useState(1);
  const [perPage] = useState(30);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async (targetPage = page) => {
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch(`/products?q=${encodeURIComponent(search)}&page=${targetPage}&per_page=${perPage}`);
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
    load(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  useEffect(() => {
    if (!selectedProduct) {
      setAttributesDraft('');
      setImagesDraft('');
      return;
    }
    setAttributesDraft(formatAttributes(selectedProduct.attributes));
    setImagesDraft(formatImageUrls(selectedProduct.image_urls));
  }, [selectedProduct]);

  const save = async (p: Product) => {
    setError('');
    try {
      const updated = await apiFetch(`/products/${p.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: p.name,
          price: p.price,
          qty: p.qty,
          availability: p.availability,
          slug: p.slug || null,
          description: p.description || null,
          attributes: parseAttributes(attributesDraft),
          image_urls: parseImageUrls(imagesDraft)
        })
      });
      setItems((prev) => prev.map((item) => (item.id === p.id ? updated : item)));
      if (selectedProduct?.id === p.id) {
        setSelectedProduct(updated);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    }
  };

  const groups = useMemo(() => {
    const unique = new Set<string>();
    for (const item of items) {
      if (item.group_name?.trim()) unique.add(item.group_name.trim());
    }
    return Array.from(unique).sort((a, b) => a.localeCompare(b, 'uk'));
  }, [items]);

  const visibleItems = useMemo(() => {
    if (selectedGroup === 'all') return items;
    return items.filter((item) => item.group_name === selectedGroup);
  }, [items, selectedGroup]);

  const pages = Math.max(1, Math.ceil(total / perPage));

  return (
    <main className="crm-layout">
      <CrmSidebar />

      <section className="crm-content products-shell card">
        <h1 style={{ marginTop: 0 }}>Каталог та товари</h1>

        <div className="row" style={{ marginBottom: 12 }}>
          <button
            onClick={async () => {
              setError('');
              try {
                await apiFetch('/prom/sync/products', { method: 'POST' });
                await load(1);
                setPage(1);
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Sync failed');
              }
            }}
          >
            Синхронізувати з Prom
          </button>
          <button className="secondary" onClick={() => load(page)}>
            Оновити
          </button>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Пошук по назві або UID"
            style={{ minWidth: 260 }}
          />
          <button
            onClick={() => {
              setPage(1);
              load(1);
            }}
          >
            Шукати
          </button>
        </div>

        {error && <p className="error">{error}</p>}
        <div className="products-workspace">
          <aside className="catalog-panel">
            <div className="catalog-panel-title">Каталог</div>
            <ul className="catalog-list">
              <li>
                <button
                  className={selectedGroup === 'all' ? 'catalog-link active' : 'catalog-link'}
                  onClick={() => setSelectedGroup('all')}
                >
                  Усі товари
                </button>
              </li>
              {groups.map((group) => (
                <li key={group}>
                  <button
                    className={selectedGroup === group ? 'catalog-link active' : 'catalog-link'}
                    onClick={() => setSelectedGroup(group)}
                  >
                    {group}
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          <div className="products-table-shell">
            {loading ? (
              <p>Завантаження...</p>
            ) : (
              <table className="products-table">
                <thead>
                  <tr>
                    <th style={{ width: 56 }}>#</th>
                    <th>Назва</th>
                    <th>Артикул</th>
                    <th>Ціна</th>
                    <th>Склад</th>
                    <th style={{ width: 54 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {visibleItems.map((p, idx) => (
                    <tr key={p.id} onDoubleClick={() => setSelectedProduct(p)}>
                      <td>{idx + 1}</td>
                      <td>{p.name}</td>
                      <td>{p.prom_uid}</td>
                      <td>{p.price.toFixed(2)}</td>
                      <td>
                        {p.qty}/{p.qty}
                      </td>
                      <td>
                        <button className="secondary small-btn" onClick={() => setSelectedProduct(p)}>
                          ▾
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

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
      </section>

      {selectedProduct && (
        <div className="product-modal-backdrop" onClick={() => setSelectedProduct(null)}>
          <div className="product-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="product-modal-head">
              <strong>Редагувати</strong>
              <button className="secondary" onClick={() => setSelectedProduct(null)}>
                ✕
              </button>
            </div>

            <div className="product-form-grid">
              <label>Назва</label>
              <input
                value={selectedProduct.name}
                onChange={(e) => setSelectedProduct((prev) => (prev ? { ...prev, name: e.target.value } : prev))}
              />

              <label>Ціна</label>
              <input
                type="number"
                min={0}
                value={selectedProduct.price}
                onChange={(e) =>
                  setSelectedProduct((prev) => (prev ? { ...prev, price: Number(e.target.value) } : prev))
                }
              />

              <label>Артикул</label>
              <input
                value={selectedProduct.prom_uid}
                onChange={(e) => setSelectedProduct((prev) => (prev ? { ...prev, prom_uid: e.target.value } : prev))}
                disabled
              />

              <label>Група</label>
              <input value={selectedProduct.group_name || 'Не вказано'} disabled />

              <label>Url адреса</label>
              <input
                value={selectedProduct.slug || ''}
                onChange={(e) => setSelectedProduct((prev) => (prev ? { ...prev, slug: e.target.value } : prev))}
                placeholder="slug-dlya-tovaru"
              />

              <label>Наявність</label>
              <select
                value={selectedProduct.availability}
                onChange={(e) =>
                  setSelectedProduct((prev) => (prev ? { ...prev, availability: e.target.value } : prev))
                }
              >
                <option value="available">available</option>
                <option value="unavailable">unavailable</option>
                <option value="preorder">preorder</option>
              </select>

              <label>Залишок</label>
              <input
                type="number"
                min={0}
                value={selectedProduct.qty}
                onChange={(e) => setSelectedProduct((prev) => (prev ? { ...prev, qty: Number(e.target.value) } : prev))}
              />
            </div>

            <div className="product-modal-note">
              <strong>Характеристики</strong>
              <textarea
                rows={5}
                value={attributesDraft}
                onChange={(e) => setAttributesDraft(e.target.value)}
                placeholder={'Розмір: M\nКолір: Чорний\nМатеріал: Нітрил'}
                style={{ width: '100%', marginTop: 8 }}
              />
            </div>

            <div className="product-modal-note">
              <strong>Картинки (по 1 URL в рядок)</strong>
              <textarea
                rows={4}
                value={imagesDraft}
                onChange={(e) => setImagesDraft(e.target.value)}
                placeholder={'https://.../image1.jpg\nhttps://.../image2.jpg'}
                style={{ width: '100%', marginTop: 8 }}
              />
            </div>

            <div className="product-modal-note">
              <strong>Опис</strong>
              <textarea
                rows={6}
                value={selectedProduct.description || ''}
                onChange={(e) =>
                  setSelectedProduct((prev) => (prev ? { ...prev, description: e.target.value } : prev))
                }
                placeholder="Текстовий опис товару..."
                style={{ width: '100%', marginTop: 8 }}
              />
            </div>

            <div className="row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
              <button className="secondary" onClick={() => setSelectedProduct(null)}>
                Скасувати
              </button>
              <button
                onClick={async () => {
                  if (!selectedProduct) return;
                  await save(selectedProduct);
                  setSelectedProduct(null);
                }}
              >
                Зберегти
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
