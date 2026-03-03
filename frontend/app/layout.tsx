import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Prom CRM',
  description: 'Admin panel for Prom products'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uk">
      <body>{children}</body>
    </html>
  );
}
