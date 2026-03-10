'use client';

import CrmSidebar from '@/components/crm-sidebar';
import { apiFetch, requireAuth } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const ORDER_STATUS_OPTIONS = [
  'Розпочато',
  'Прийняте',
  'Не дозвон',
  'Очікування оплати',
  'Оплачений',
  'Очікує ТТН',
  'Очікує відправки',
  'Очікування відповіді Вайбер',
  'Скасоване',
  'Завершене'
] as const;

const ORDER_STATUS_LABELS: Record<string, string> = {
  new: 'Розпочато',
  pending: 'Розпочато',
  processing: 'Прийняте',
  accepted: 'Прийняте',
  received: 'Прийняте',
  not_called: 'Не дозвон',
  pending_payment: 'Очікування оплати',
  awaiting_payment: 'Очікування оплати',
  paid: 'Оплачений',
  ttn_pending: 'Очікує ТТН',
  awaiting_ttn: 'Очікує ТТН',
  shipping_pending: 'Очікує відправки',
  awaiting_shipping: 'Очікує відправки',
  viber_pending: 'Очікування відповіді Вайбер',
  awaiting_viber_reply: 'Очікування відповіді Вайбер',
  cancelled: 'Скасоване',
  canceled: 'Скасоване',
  done: 'Завершене',
  completed: 'Завершене',
  delivered: 'Завершене'
};

type OrderItem = {
  id: number;
  name: string;
  sku?: string | null;
  product_prom_uid?: string | null;
  quantity: number;
  price: number;
  line_total: number;
};

type Order = {
  id: number;
  prom_uid: string;
  status: string;
  total_price: number;
  currency: string;
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_email?: string | null;
  payment_method?: string | null;
  shipping_method?: string | null;
  shipping_address?: string | null;
  shipping_city?: string | null;
  shipping_branch?: string | null;
  comment?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
};

function displayOrderStatus(status: string) {
  return ORDER_STATUS_LABELS[status.trim().toLowerCase()] || status;
}

export default function OrdersPage() {
  const router = useRouter();
  const [items, setItems] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [activeStatus, setActiveStatus] = useState<string>('Всі');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [updatingOrderId, setUpdatingOrderId] = useState<number | null>(null);

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

  const saveOrder = async () => {
    if (!selectedOrder) return;
    setSaving(true);
    setError('');
    try {
      const updated = await apiFetch(`/orders/${selectedOrder.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: selectedOrder.status,
          customer_name: selectedOrder.customer_name || null,
          customer_phone: selectedOrder.customer_phone || null,
          customer_email: selectedOrder.customer_email || null,
          payment_method: selectedOrder.payment_method || null,
          shipping_method: selectedOrder.shipping_method || null,
          shipping_address: selectedOrder.shipping_address || null,
          shipping_city: selectedOrder.shipping_city || null,
          shipping_branch: selectedOrder.shipping_branch || null,
          comment: selectedOrder.comment || null
        })
      });
      setItems((prev) => prev.map((order) => (order.id === updated.id ? updated : order)));
      setSelectedOrder(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const updateOrderStatus = async (orderId: number, status: string) => {
    setUpdatingOrderId(orderId);
    setError('');
    try {
      const updated = await apiFetch(`/orders/${orderId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      });
      setItems((prev) => prev.map((order) => (order.id === updated.id ? updated : order)));
      setSelectedOrder((prev) => (prev && prev.id === updated.id ? updated : prev));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Status update failed');
    } finally {
      setUpdatingOrderId(null);
    }
  };

  useEffect(() => {
    if (!requireAuth(router.push)) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statusCounts = ORDER_STATUS_OPTIONS.reduce<Record<string, number>>((acc, status) => {
    acc[status] = 0;
    return acc;
  }, {});

  for (const order of items) {
    const normalizedStatus = displayOrderStatus(order.status);
    if (normalizedStatus in statusCounts) {
      statusCounts[normalizedStatus] += 1;
    }
  }

  const visibleOrders = activeStatus === 'Всі'
    ? items
    : items.filter((order) => displayOrderStatus(order.status) === activeStatus);

  return (
    <main className="crm-layout">
      <CrmSidebar />

      <section className="crm-content orders-shell card">
        <h1 style={{ marginTop: 0 }}>Замовлення</h1>

        <div className="row" style={{ marginBottom: 16 }}>
          <button onClick={syncOrders}>Синхронізувати замовлення з Prom</button>
          <button className="secondary" onClick={load}>
            Оновити список
          </button>
        </div>

        <div className="order-status-tabs">
          <button
            className={activeStatus === 'Всі' ? 'order-status-tab active' : 'order-status-tab'}
            onClick={() => setActiveStatus('Всі')}
          >
            Всі
            <span className="order-status-count">{items.length}</span>
          </button>
          {ORDER_STATUS_OPTIONS.map((status) => (
            <button
              key={status}
              className={activeStatus === status ? 'order-status-tab active' : 'order-status-tab'}
              onClick={() => setActiveStatus(status)}
            >
              {status}
              <span className="order-status-count">{statusCounts[status]}</span>
            </button>
          ))}
        </div>

        {error && <p className="error">{error}</p>}
        {loading ? (
          <p>Завантаження...</p>
        ) : (
          <div className="orders-table-shell">
            <table className="orders-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Замовлення</th>
                  <th>Клієнт</th>
                  <th>Статус</th>
                  <th>Сума</th>
                  <th>Дата</th>
                  <th style={{ width: 180 }}></th>
                </tr>
              </thead>
              <tbody>
                {visibleOrders.map((order) => (
                  <tr key={order.id} onClick={() => setSelectedOrder(order)} className="order-list-row">
                    <td>{order.id}</td>
                    <td>#{order.prom_uid}</td>
                    <td>
                      {order.customer_name || '-'}
                      {order.customer_phone ? ` (${order.customer_phone})` : ''}
                    </td>
                    <td>{displayOrderStatus(order.status)}</td>
                    <td>
                      {order.total_price} {order.currency}
                    </td>
                    <td>{new Date(order.created_at).toLocaleString('uk-UA')}</td>
                    <td>
                      <div className="order-row-actions">
                        <select
                          value={displayOrderStatus(order.status)}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                          disabled={updatingOrderId === order.id}
                          className="order-row-status"
                        >
                          {ORDER_STATUS_OPTIONS.map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedOrder && (
        <div className="order-modal-backdrop" onClick={() => setSelectedOrder(null)}>
          <div className="order-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="order-modal-topbar">
              <div className="order-modal-title">
                Замовлення {selectedOrder.prom_uid} від {new Date(selectedOrder.created_at).toLocaleString('uk-UA')}
              </div>
              <button className="secondary" onClick={() => setSelectedOrder(null)}>
                ✕
              </button>
            </div>

            <div className="order-items-shell">
              <table className="order-items-table">
                <thead>
                  <tr>
                    <th style={{ width: 52 }}>#</th>
                    <th>Назва</th>
                    <th>Артикул</th>
                    <th>Кількість</th>
                    <th>Ціна</th>
                    <th>Сума</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedOrder.items.map((item, index) => (
                    <tr key={item.id}>
                      <td>{index + 1}</td>
                      <td>{item.name}</td>
                      <td>{item.sku || item.product_prom_uid || '-'}</td>
                      <td>{item.quantity}</td>
                      <td>{item.price}</td>
                      <td>{item.line_total}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={3}></td>
                    <td>{selectedOrder.items.reduce((sum, item) => sum + item.quantity, 0)}</td>
                    <td></td>
                    <td>{selectedOrder.total_price}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="order-edit-layout">
              <div className="order-section-title">Клієнт</div>
              <div className="order-field-grid">
                <label>Телефон</label>
                <input
                  value={selectedOrder.customer_phone || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, customer_phone: e.target.value } : prev))
                  }
                />

                <label>Ім'я</label>
                <input
                  value={selectedOrder.customer_name || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, customer_name: e.target.value } : prev))
                  }
                />

                <label>Email</label>
                <input
                  value={selectedOrder.customer_email || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, customer_email: e.target.value } : prev))
                  }
                />

                <label>Статус</label>
                <select
                  value={displayOrderStatus(selectedOrder.status)}
                  onChange={(e) => setSelectedOrder((prev) => (prev ? { ...prev, status: e.target.value } : prev))}
                >
                  {ORDER_STATUS_OPTIONS.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </div>

              <div className="order-section-title">Оплата та доставка</div>
              <div className="order-field-grid">
                <label>Спосіб оплати</label>
                <input
                  value={selectedOrder.payment_method || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, payment_method: e.target.value } : prev))
                  }
                />

                <label>Спосіб доставки</label>
                <input
                  value={selectedOrder.shipping_method || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, shipping_method: e.target.value } : prev))
                  }
                />

                <label>Адреса доставки</label>
                <input
                  value={selectedOrder.shipping_address || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, shipping_address: e.target.value } : prev))
                  }
                />

                <label>Місто</label>
                <input
                  value={selectedOrder.shipping_city || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, shipping_city: e.target.value } : prev))
                  }
                />

                <label>Відділення</label>
                <input
                  value={selectedOrder.shipping_branch || ''}
                  onChange={(e) =>
                    setSelectedOrder((prev) => (prev ? { ...prev, shipping_branch: e.target.value } : prev))
                  }
                />
              </div>

              <div className="order-section-title">Коментар</div>
              <textarea
                rows={4}
                value={selectedOrder.comment || ''}
                onChange={(e) => setSelectedOrder((prev) => (prev ? { ...prev, comment: e.target.value } : prev))}
                className="order-comment"
              />
            </div>

            <div className="row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
              <button className="secondary" onClick={() => setSelectedOrder(null)}>
                Скасувати
              </button>
              <button onClick={saveOrder} disabled={saving}>
                {saving ? 'Збереження...' : 'Зберегти'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
