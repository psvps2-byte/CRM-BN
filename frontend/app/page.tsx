import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="container">
      <div className="card">
        <h1>Prom CRM</h1>
        <p className="muted">Оберіть розділ адмін-панелі.</p>
        <nav>
          <Link href="/products">Товари</Link>
          <Link href="/inventory">Склад</Link>
          <Link href="/orders">Замовлення</Link>
          <Link href="/login">Логін</Link>
        </nav>
      </div>
    </main>
  );
}
