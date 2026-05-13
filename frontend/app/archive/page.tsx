import Link from 'next/link';
import { db } from '@/db';
import { articles } from '@/db/schema';
import { desc, lt } from 'drizzle-orm';
import { format, subHours } from 'date-fns';

export default async function ArchivePage() {
  let oldArticles: any[] = [];
  
  try {
    const yesterday = subHours(new Date(), 24);
    oldArticles = await db.select()
      .from(articles)
      .where(lt(articles.pub_date, yesterday))
      .orderBy(desc(articles.pub_date));
  } catch (error) {
    console.error("Archive fetch error:", error);
  }

  // Group by date
  const groupedByDate: Record<string, any[]> = {};
  oldArticles.forEach(article => {
    const dateKey = format(article.pub_date, 'MMMM d, yyyy');
    if (!groupedByDate[dateKey]) groupedByDate[dateKey] = [];
    groupedByDate[dateKey].push(article);
  });

  return (
    <>
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Archive</h1>
            <p>Historical intelligence beyond the 24-hour signal window.</p>
          </div>
          <Link href="/" className="pill">&larr; Back to Signal</Link>
        </div>
      </header>

      <main>
        {oldArticles.length === 0 ? (
          <div className="empty-state">
            <h3>Archive Empty</h3>
            <p>Signals older than 24 hours will appear here automatically.</p>
          </div>
        ) : (
          Object.entries(groupedByDate).map(([date, items]) => (
            <section key={date} className="section">
              <div className="section-header">
                <span className="section-tag">{date}</span>
                <div className="section-line" />
                <span className="section-count">{items.length} articles</span>
              </div>
              <div className="card-grid">
                {items.map((article) => (
                  <Link href={`/article/${article.id}`} key={article.id} className="card">
                    <span className="card-source">{article.source_name}</span>
                    <h3 className="card-title">{article.headline}</h3>
                    <div className="card-footer">
                      <span>{article.tags?.[0] || '#General'}</span>
                      <time>{format(article.pub_date, 'h:mm a')}</time>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))
        )}
      </main>
    </>
  );
}
