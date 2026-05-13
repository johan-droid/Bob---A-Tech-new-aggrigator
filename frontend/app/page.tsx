import Link from 'next/link';
import { db } from '@/db';
import { articles } from '@/db/schema';
import { desc, gt, sql } from 'drizzle-orm';
import { subHours } from 'date-fns';
import { AnimatedCounter, LiveClock, InteractiveFeed, ScrollToTop } from './components';

export const revalidate = 60;

export default async function HomePage() {
  let latestArticles: any[] = [];
  let totalCount = 0;
  let sourceCount = 0;
  let isConnected = true;

  try {
    const yesterday = subHours(new Date(), 24);
    latestArticles = await db.select()
      .from(articles)
      .where(gt(articles.pub_date, yesterday))
      .orderBy(desc(articles.pub_date));

    const countResult = await db.select({ count: sql<number>`count(*)` }).from(articles);
    totalCount = Number(countResult[0]?.count || 0);

    const sources = new Set(latestArticles.map(a => a.source_name));
    sourceCount = sources.size;
  } catch (error) {
    isConnected = false;
  }

  const sectionCount = new Set(latestArticles.map(a => a.tags?.[0] || '#General')).size;

  // Serialize for client component
  const serializedArticles = latestArticles.map(a => ({
    ...a,
    pub_date: a.pub_date.toISOString(),
  }));

  return (
    <>
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Intelligence Signal</h1>
            <p>
              Curated signals from {sourceCount || '8+'} sources &bull; <LiveClock />
            </p>
          </div>
          <Link href="/archive" className="pill">🗄️ Browse Archive</Link>
        </div>
      </header>

      {isConnected && (
        <div className="stats-bar">
          <AnimatedCounter value={latestArticles.length} label="Signals (24h)" />
          <AnimatedCounter value={sectionCount} label="Categories" />
          <AnimatedCounter value={sourceCount} label="Sources Active" />
          <AnimatedCounter value={totalCount} label="Total Indexed" />
        </div>
      )}

      <main>
        {!isConnected ? (
          <div className="empty-state">
            <h3>Neural Link Inactive</h3>
            <p>Add your <code>DATABASE_URL</code> to <code>.env.local</code> to connect the intelligence pipeline.</p>
          </div>
        ) : latestArticles.length === 0 ? (
          <div className="empty-state">
            <h3>No Signals Detected</h3>
            <p>The crawler hasn't captured new intelligence this cycle. <Link href="/archive" style={{ color: 'var(--accent)', textDecoration: 'underline' }}>Explore the archive</Link>.</p>
          </div>
        ) : (
          <InteractiveFeed articles={serializedArticles} />
        )}
      </main>

      <ScrollToTop />
    </>
  );
}
