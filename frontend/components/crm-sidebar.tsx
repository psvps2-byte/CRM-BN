'use client';

import { clearToken } from '@/lib/api';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/orders', label: 'Замовлення' },
  { href: '/products', label: 'Каталог та товари' },
  { href: '/inventory', label: 'Журнал складських дій' }
];

export default function CrmSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="crm-sidebar">
      <div className="crm-brand">BeautyNikopol</div>
      <div className="crm-section-title">CRM</div>
      <nav className="crm-menu" aria-label="CRM Navigation">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`crm-menu-link ${pathname.startsWith(item.href) ? 'active' : ''}`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="crm-sidebar-footer">
        <button
          type="button"
          className="crm-logout-btn"
          onClick={() => {
            clearToken();
            router.push('/login');
          }}
        >
          Вийти
        </button>
      </div>
    </aside>
  );
}
