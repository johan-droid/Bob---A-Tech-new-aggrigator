import Link from 'next/link';
import { db } from '@/db';
import { articles } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { notFound } from 'next/navigation';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let article;
  try {
    const results = await db.select().from(articles).where(eq(articles.id, id));
    article = results[0];
  } catch (error) {
    console.error("Database fetch error:", error);
  }

  if (!article) {
    notFound();
  }

  const readingTime = article.content ? Math.ceil(article.content.split(' ').length / 225) : 1;

  return (
    <article className="reader">
      <Link href="/" className="reader-back">
        <span>&larr;</span> Back to Signal
      </Link>

      <h1>{article.headline}</h1>

      <div className="reader-meta">
        <strong>{article.source_name}</strong>
        <span>&bull;</span>
        <span>{format(article.pub_date, 'MMMM d, yyyy')}</span>
        <span>&bull;</span>
        <span>{readingTime} min read</span>
      </div>

      <div className="reader-body">
        <div className="reader-disclaimer">
          {article.disclaimer_text || 'This intelligence signal is aggregated for informational purposes. All rights belong to original publishers.'}
        </div>

        {article.summary && (
          <div className="reader-pullquote">
            {article.summary}
          </div>
        )}
        
        <div className="reader-content">
          {article.content ? (
            <ReactMarkdown>{article.content}</ReactMarkdown>
          ) : (
            <div className="reader-fallback">
              <h3>Signal Synthesis in Progress</h3>
              <p>Bob's intelligence engine is currently processing the full depth of this signal. You can view the raw intelligence at the source while we complete the synthesis.</p>
            </div>
          )}
        </div>
      </div>

      <a href={article.original_url} target="_blank" rel="noopener noreferrer" className="reader-source-link">
        View Original Source &nearrow;
      </a>
    </article>
  );
}
