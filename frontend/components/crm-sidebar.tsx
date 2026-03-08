'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/orders', label: 'Замовлення' },
  { href: '/products', label: 'Каталог та товари' },
  { href: '/inventory', label: 'Журнал складських дій' }
];

export default function CrmSidebar() {
  const pathname = usePathname();

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
    </aside>
  );
}
