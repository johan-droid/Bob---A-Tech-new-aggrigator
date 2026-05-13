import type { Metadata } from 'next';
import { Inter, Playfair_Display, JetBrains_Mono } from 'next/font/google';
import Link from 'next/link';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const playfair = Playfair_Display({ subsets: ['latin'], variable: '--font-playfair' });
const jetbrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains' });

export const metadata: Metadata = {
  title: 'Bob — Intelligence Aggregator',
  description: 'A SaaS-grade news intelligence system. Curated technical signals from 8+ high-fidelity sources.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className={`${inter.variable} ${playfair.variable} ${jetbrains.variable}`}>
      <body className={inter.className}>
        <div className="app-shell">
          <nav className="topbar">
            <Link href="/" className="topbar-brand">
              <div className="topbar-logo">B</div>
              <span className="topbar-name">Bob</span>
            </Link>

            <div className="topbar-nav">
              <Link href="/" className="topbar-link active">Signal</Link>
              <Link href="/archive" className="topbar-link">Archive</Link>
              <Link href="/disclaimer" className="topbar-link">About</Link>
            </div>

            <div className="topbar-status">
              <span className="status-dot"></span>
              Crawler Active
            </div>
          </nav>

          <div className="main-content">
            {children}
          </div>

          <footer className="app-footer">
            <div className="footer-links">
              <Link href="/">Signal</Link>
              <Link href="/archive">Archive</Link>
              <Link href="/disclaimer">Disclaimer</Link>
            </div>
            <p>&copy; {new Date().getFullYear()} Bob Intelligence Aggregator</p>
          </footer>
        </div>
      </body>
    </html>
  );
}
